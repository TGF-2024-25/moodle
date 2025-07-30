<?php
require_once('../../config.php');
require_login();

// Manejo de subida de archivos del estudiante
$id = required_param('id', PARAM_INT);  // Obtener ID del módulo
$cm = get_coursemodule_from_id('autocorreccion', $id, 0, false, MUST_EXIST);
$course = get_course($cm->course);
$context = context_module::instance($cm->id);

require_course_login($course, true, $cm);

$PAGE->set_context($context);
$PAGE->set_url('/mod/autocorreccion/upload.php', ['id' => $id]);
$PAGE->set_title("Subida de archivo (.ipynb)");
$PAGE->set_heading(format_string($course->fullname));

echo $OUTPUT->header();

// Configuración de rutas
$upload_dir = __DIR__ . "/uploads/";
$nbgrader_dir = "/home/vagrant/mycourse"; // Ruta corregida

// Crear directorio de subidas si no existe
if (!is_dir($upload_dir)) {
    mkdir($upload_dir, 0777, true);
    chmod($upload_dir, 0777);
}

if ($_FILES['file']['error'] === UPLOAD_ERR_OK) {
    $ext = pathinfo($_FILES['file']['name'], PATHINFO_EXTENSION);
    $filename = $USER->id . '_' . time() . '.' . $ext;    

    // Validar extensión
    $allowed_ext = ['ipynb'];
    if (!in_array($ext, $allowed_ext)) {
        echo $OUTPUT->notification("Solo se permiten archivos .ipynb", 'error');
        echo $OUTPUT->footer();
        exit;
    }

    $target_file = $upload_dir . $filename;

    if (move_uploaded_file($_FILES['file']['tmp_name'], $target_file)) {
        echo $OUTPUT->notification("Archivo subido correctamente: " . s($filename), 'success');

        // Preparar estructura NBGrader
        $dest_path = "$nbgrader_dir/submitted/$USER->username/ps1";
        if (!is_dir($dest_path)) {
            mkdir($dest_path, 0777, true);
            chmod($dest_path, 0777);
        }

        // Copiar archivo a NBGrader
        $nbgrader_file = "$dest_path/problem1.ipynb";
        if (!copy($target_file, $nbgrader_file)) {
            echo $OUTPUT->notification("Error al copiar el archivo a NBGrader", 'error');
            echo $OUTPUT->footer();
            exit;
        }
        chmod($nbgrader_file, 0666);

        // Ejecutar NBGrader con entorno virtual y permisos adecuados
        $command = "sudo -u vagrant /home/vagrant/nbgrader_env/bin/python " .
                   "/var/www/html/moodle/mod/autocorreccion/evaluate_nbgrader.py " .
                   escapeshellarg($nbgrader_file) . " " .
                   escapeshellarg($USER->username) . " 2>&1";

        $output = shell_exec($command);
        $result = json_decode($output, true);

        // Procesar resultados
        if ($result && isset($result['estado']) && $result['estado'] === 'ok') {
            $nota = (float)$result['nota'];
            $feedback = $result['retroalimentacion'];
            
            echo "<div class='alert alert-success'><strong>Nota:</strong> $nota</div>";
            echo "<details class='mt-3'><summary class='btn btn-secondary'>Ver feedback detallado</summary>";
            echo "<div class='p-3 mt-2 bg-light border rounded' style='white-space: pre-wrap;'>" . s($feedback) . "</div></details>";
        } else {
            $error_msg = $result['error'] ?? $output;
            echo $OUTPUT->notification("Error en la corrección: " . s($error_msg), 'error');
            $nota = 0;
            $feedback = "Error en la corrección automática: " . s($error_msg);
        }

        // Guardar en la base de datos
        $record = new stdClass();
        $record->userid = $USER->id;
        $record->autocorreccionid = $cm->instance;
        $record->nota = $nota;
        // $rawfeedback = $result['retroalimentacion'];
        // $record->feedback = is_array($rawfeedback) ? implode("\n", $rawfeedback) : $rawfeedback;
        $record->feedback = $feedback;
        $record->files = json_encode([$filename]);
        $record->timecreated = time();
        $record->timemodified = time();

        try {
            $DB->insert_record('autocorreccion_envios', $record);
            
            // Actualizar calificación en Moodle
            $graderecord = [
                'userid' => $USER->id,
                'rawgrade' => $nota,
                'feedback' => $feedback,
                'feedbackformat' => FORMAT_PLAIN
            ];
            
            $params = [
                'itemname' => 'Autocorrección Notebook',
                'idnumber' => $cm->id
            ];
            
            $grade_result = grade_update(
                'mod/autocorreccion',
                $course->id,
                'mod',
                'autocorreccion',
                $cm->instance,
                0,
                $graderecord,
                $params
            );
            
            if ($grade_result !== GRADE_UPDATE_OK) {
                echo $OUTPUT->notification("La nota se guardó pero hubo un problema al actualizar el libro de calificaciones", 'notifyproblem');
            }
        } catch (Exception $e) {
            echo $OUTPUT->notification("Error al guardar en la base de datos: " . $e->getMessage(), 'error');
        }
    } else {
        echo $OUTPUT->notification("Error al subir el archivo", 'error');
    }
} else {
    echo $OUTPUT->notification("Error en la subida del archivo: Código " . $_FILES['file']['error'], 'error');
}

echo $OUTPUT->footer();
?>