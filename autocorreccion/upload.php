<?php
require_once('../../config.php');
require_login();

$id = required_param('id', PARAM_INT);  // Obtener ID del módulo
$cm = get_coursemodule_from_id('autocorreccion', $id, 0, false, MUST_EXIST);
$course = get_course($cm->course);
$context = context_module::instance($cm->id);

require_course_login($course, true, $cm);

$PAGE->set_url('/mod/autocorreccion/upload.php', ['id' => $id]);
$PAGE->set_title("Subida de archivo");
$PAGE->set_heading(format_string($course->fullname));

echo $OUTPUT->header();

$upload_dir = __DIR__ . "/uploads/";
if (!is_dir($upload_dir)) {
    mkdir($upload_dir, 0777, true);
}

if ($_FILES['file']['error'] === UPLOAD_ERR_OK) {
    $ext = pathinfo($_FILES['file']['name'], PATHINFO_EXTENSION);
    $filename = $USER->id . '_' . time() . '.' . $ext;    

    $allowed_ext = ['py'];
    if (!in_array($ext, $allowed_ext)) {
        echo "<p>Solo se permiten archivos .py</p>";
        echo $OUTPUT->footer();
        exit;
    }

    $target_file = $upload_dir . $filename;

    if (move_uploaded_file($_FILES['file']['tmp_name'], $target_file)) {
        echo "<p>Archivo subido correctamente: <strong>$filename</strong></p>";

        // Ejecutar el script de evaluación (evaluate.py)
        $command = escapeshellcmd("python3 " . __DIR__ . "/evaluate.py") . ' ' . escapeshellarg($target_file);
        $output = shell_exec($command);

        echo "<pre>📝 Resultados de la corrección:\n$output</pre>";

        // Guardar en la base de datos
        global $DB, $USER;

        // Intentar extraer nota con regex (ej: "Nota: 8.5/10")
        $nota = null;
        // Intentamos extraer la nota del resultado
        if (preg_match('/[Nn]ota[:\s]+([0-9]+(?:\.[0-9]+)?)/', $output, $matches)) {
            $nota = floatval($matches[1]);
        }

        // Si no se extrae la nota con regex, asignamos una calificación por defecto (opcional)
        if ($nota === null) {
            $nota = 0; // Puedes cambiar esto según tu lógica
        }

        // Crear un nuevo registro en la tabla de envíos
        $record = new stdClass();
        $record->userid = $USER->id;
        $record->autocorreccionid = $cm->instance;
        $record->curso = $nota;  // Guardar la calificación
        $record->feedback = $output; // Guardar el feedback
        $record->filename = $filename;
        $record->timecreated = time();

        // Insertar el envío en la base de datos
        $DB->insert_record('autocorreccion_envios', $record);

        // Actualizar la calificación en el libro de calificaciones de Moodle
        // Verificar que la calificación es válida antes de actualizar el libro de calificaciones
        if (is_numeric($nota)) {
            grade_update(
                'mod/autocorreccion',  // Componente
                $course->id,           // ID del curso
                'mod',                 // Tipo de actividad
                'autocorreccion',      // Nombre del módulo
                $cm->instance,         // ID de la instancia del módulo
                $USER->id,             // ID del usuario
                ['finalgrade' => $nota] // Nueva calificación
            );
        }
        
    } else {
        echo "<p>Error al subir el archivo.</p>";
    }
} else {
    echo "<p> Error en la subida del archivo.</p>";
}

echo $OUTPUT->footer();
?>
