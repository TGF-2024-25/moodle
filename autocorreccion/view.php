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

/* // Mostrar imagen antes de cualquier contenido
$imageurl = $OUTPUT->pix_url('imagen_icono', 'mod_autocorreccion'); // Ruta de la imagen subida en /pix/image_icono.jpg
echo '<div style="text-align:center;">';
echo '<img src="' . $imageurl . '" alt="Imagen del plugin" style="width:300px;height:auto;"/>';
echo '</div>' */

echo $OUTPUT->header();

global $DB, $USER;

// Mostrar formulario de subida de archivo
echo "<h2>Sube tu archivo para corrección</h2>";
echo '<form action="upload.php" method="post" enctype="multipart/form-data">
        <input type="hidden" name="id" value="' . $id . '">
        <input type="file" name="file" accept=".py" required>
        <input type="submit" value="Subir y Corregir">
      </form>';

// Obtener los registros de este usuario para esta instancia del módulo
$records = $DB->get_records('autocorreccion_envios', [
    'userid' => $USER->id,
    'autocorreccionid' => $cm->instance
], 'timecreated DESC');

// Calcular estadísticas simples
$num_envios = count($records);
$mejor_nota = null;
$suma_notas = 0;
$ultima_fecha = null;

foreach ($records as $r) {
    if (is_numeric($r->curso)) {
        $suma_notas += $r->curso;
        if ($mejor_nota === null || $r->curso > $mejor_nota) {
            $mejor_nota = $r->curso;
        }
    }
    if ($ultima_fecha === null || $r->timecreated > $ultima_fecha) {
        $ultima_fecha = $r->timecreated;
    }
}

$nota_media = $num_envios > 0 ? round($suma_notas / $num_envios, 2) : 'N/A';
$ultima_fecha_formateada = $ultima_fecha ? date('d/m/Y H:i', $ultima_fecha) : 'N/A';

// Mostrar estadísticas
if ($num_envios > 0) {
    echo '<div style="margin-top: 20px; padding: 10px; border: 1px solid #ccc; background-color: #f9f9f9;">
            <h4>Estadísticas de tus envíos</h4>
            <ul>
                <li><strong>Total de envíos:</strong> ' . $num_envios . '</li>
                <li><strong>Nota media:</strong> ' . $nota_media . '</li>
                <li><strong>Mejor nota:</strong> ' . ($mejor_nota !== null ? $mejor_nota : 'N/A') . '</li>
                <li><strong>Último envío:</strong> ' . $ultima_fecha_formateada . '</li>
            </ul>
          </div>';
}

// Mostrar tabla con envíos
echo '<h3>Tus correcciones anteriores</h3>';
if (empty($records)) {
    echo "<p>Aún no has hecho ninguna corrección.</p>";
} else {
    echo '<table class="generaltable">';
    echo '<thead><tr><th>Fecha</th><th>Nota</th><th>Resultado</th></tr></thead><tbody>';

    foreach ($records as $r) {
        // Formatear la fecha de creación
        $fecha = date('d/m/Y H:i', $r->timecreated);

        // Convertir el feedback para evitar problemas con caracteres especiales y saltos de línea
        $feedback = nl2br(s($r->feedback));

        // Mostrar la nota guardada
        $nota = isset($r->curso) ? $r->curso : 'N/A';

        // Mostrar el nombre del archivo, si está disponible
        $archivo = isset($r->filename) ? $r->filename : 'No registrado';

        echo "<tr>
                <td>$fecha</td>
                <td>$nota</td>
                <td><strong>Archivo:</strong> $archivo<br>$feedback</td>
              </tr>";
    }

    echo '</tbody></table>';
}

echo $OUTPUT->footer();
?>
