<?php
require_once(__DIR__ . '/../../config.php');
require_login();

$PAGE->set_url('/mod/autocorreccion/index.php');
$PAGE->set_title('Corrección Automática');
$PAGE->set_heading('Corrección Automática de Tareas');

echo $OUTPUT->header();
echo "<h2>Sube tus archivos para corrección</h2>";

echo '<form action="upload.php" method="post" enctype="multipart/form-data">
        <input type="file" name="files[]" multiple accept=".py,.ipynb" required>
        <input type="submit" value="Subir y Corregir" class="btn btn-primary">
      </form>';

echo $OUTPUT->footer();
?>