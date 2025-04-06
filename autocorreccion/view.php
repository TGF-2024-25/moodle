<?php
require_once('../../config.php');
require_login();

$id = required_param('id', PARAM_INT);  // Obtener ID del módulo
$cm = get_coursemodule_from_id('autocorreccion', $id, 0, false, MUST_EXIST);
$course = get_course($cm->course);
$context = context_module::instance($cm->id);

require_course_login($course, true, $cm);

$PAGE->set_url('/mod/autocorreccion/view.php', ['id' => $id]);
$PAGE->set_title('Resultados de Corrección');
$PAGE->set_heading(format_string($course->fullname));

echo $OUTPUT->header();

global $DB, $USER;

// Mostrar formulario de subida de archivo
echo "<h2>📝 Sube tu archivo para corrección</h2>";
echo '<form action="upload.php" method="post" enctype="multipart/form-data">
        <input type="hidden" name="id" value="' . $id . '">
        <input type="file" name="file" accept=".py" required>
        <input type="submit" value="Subir y Corregir">
      </form>';

// Obtener los registros de este usuario ordenados por fecha (más recientes primero)
$records = $DB->get_records('autocorreccion_envios', ['userid' => $USER->id], 'timecreated DESC');

echo '<h3>📝 Tus correcciones anteriores</h3>';
if (empty($records)) {
    echo "<p>📭 Aún no has hecho ninguna corrección.</p>";
} else {
    echo '<table class="generaltable">';
    echo '<thead><tr><th>Fecha</th><th>Nota</th><th>Resultado</th></tr></thead><tbody>';

    foreach ($records as $r) {
        // Formatear la fecha de creación
        $fecha = date('d/m/Y H:i', $r->timecreated);
        // Convertir el feedback para evitar problemas con caracteres especiales y saltos de línea
        $feedback = nl2br(s($r->feedback)); 

        // Mostrar la nota guardada
        $nota = isset($r->curso) ? $r->curso : 'N/A';  // Si no hay nota, mostrar 'N/A'

        echo "<tr><td>$fecha</td><td>$nota</td><td>$feedback</td></tr>";
    }

    echo '</tbody></table>';
}

echo $OUTPUT->footer();
?>
