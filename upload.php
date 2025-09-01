<?php
require_once('../../config.php');
require_login();

// Manejo de subida de archivos del estudiante
$id = required_param('id', PARAM_INT);
$cm = get_coursemodule_from_id('autocorreccion', $id, 0, false, MUST_EXIST);
$course = get_course($cm->course);
$context = context_module::instance($cm->id);

require_course_login($course, true, $cm);

$PAGE->set_context($context);
$PAGE->set_url('/mod/autocorreccion/upload.php', ['id' => $id]);
$PAGE->set_title("Subida de archivos de programación");
$PAGE->set_heading(format_string($course->fullname));

echo $OUTPUT->header();

// Configuración de rutas
$upload_dir = __DIR__ . "/uploads/";
$nbgrader_dir = "/home/vagrant/mycourse";
$temp_dir = sys_get_temp_dir() . '/autocorreccion_' . $USER->id;

// Crear directorios si no existen
if (!is_dir($upload_dir)) {
    if (!mkdir($upload_dir, 0777, true)) {
        throw new Exception("No se pudo crear el directorio de uploads");
    }
}
if (!is_dir($temp_dir)) {
    if (!mkdir($temp_dir, 0777, true)) {
        throw new Exception("No se pudo crear el directorio temporal");
    }
}

function convertir_py_a_ipynb($archivo_py) {
    global $temp_dir;
    
    $nombre_base = pathinfo($archivo_py, PATHINFO_FILENAME);
    $archivo_ipynb = $temp_dir . '/' . $nombre_base . '.ipynb';
    
    // Verificar que el script de conversión existe
    $script_path = "/var/www/html/moodle/mod/autocorreccion/convert_py_to_ipynb.py";
    if (!file_exists($script_path)) {
        throw new Exception("El script de conversión no existe en: $script_path");
    }
    
    // Usar el script de conversión Python
    $command = "/home/vagrant/nbgrader_env/bin/python " . 
               $script_path . " " .
               escapeshellarg($archivo_py) . " " .
               escapeshellarg($archivo_ipynb) . " 2>&1";
    
    error_log("Ejecutando comando: $command");
    exec($command, $output, $return_code);
    
    if ($return_code !== 0) {
        $error_msg = "Error al convertir archivo (código $return_code): " . implode("\n", $output);
        error_log($error_msg);
        throw new Exception($error_msg);
    }
    
    if (!file_exists($archivo_ipynb)) {
        throw new Exception("El archivo convertido no se generó en: $archivo_ipynb");
    }
    
    return $archivo_ipynb;
}

function procesar_archivo($archivo, $es_python = false) {
    global $USER, $nbgrader_dir, $temp_dir;
    
    $nombre_archivo = $USER->id . '_' . time() . '_' . basename($archivo);
    $destino_final = $nbgrader_dir . '/submitted/' . $USER->username . '/ps1/' . $nombre_archivo;
    
    // Crear directorio de destino si no existe
    $destino_dir = dirname($destino_final);
    if (!is_dir($destino_dir)) {
        mkdir($destino_dir, 0777, true);
    }
    
    // Para archivos Python, primero convertimos
    if ($es_python) {
        $archivo = convertir_py_a_ipynb($archivo);
        $nombre_archivo = pathinfo($nombre_archivo, PATHINFO_FILENAME) . '.ipynb';
        $destino_final = $nbgrader_dir . '/submitted/' . $USER->username . '/ps1/' . $nombre_archivo;
    }
    
    // Copiar archivo a NBGrader
    if (!copy($archivo, $destino_final)) {
        throw new Exception("Error al copiar el archivo a NBGrader: " . error_get_last()['message']);
    }
    chmod($destino_final, 0666);
    
    // Ejecutar NBGrader
    $command = "sudo -u vagrant /home/vagrant/nbgrader_env/bin/python " .
               "/var/www/html/moodle/mod/autocorreccion/evaluate_nbgrader.py " .
               escapeshellarg($destino_final) . " " .
               escapeshellarg($USER->username) . " 2>&1";
    
    $output = shell_exec($command);
    $result = json_decode($output, true);
    
    if (!$result) {
        throw new Exception("La evaluación devolvió un formato inválido: " . substr($output, 0, 200));
    }
    
    if (!isset($result['estado']) || $result['estado'] !== 'ok') {
        throw new Exception($result['error'] ?? "Error desconocido al evaluar");
    }
    
    return [
        'nota' => (float)$result['nota'],
        'feedback' => $result['retroalimentacion'],
        'archivo' => $nombre_archivo
    ];
}

try {
    if (empty($_FILES['files']['name'][0])) {
        throw new Exception("No se han subido archivos");
    }

    $notas = [];
    $feedbacks = [];
    $archivos_subidos = [];

    foreach ($_FILES['files']['tmp_name'] as $key => $tmp_name) {
        if ($_FILES['files']['error'][$key] !== UPLOAD_ERR_OK) {
            echo $OUTPUT->notification("Error en archivo {$_FILES['files']['name'][$key]}: " . 
                 $this->get_upload_error_message($_FILES['files']['error'][$key]), 'notifyproblem');
            continue;
        }

        $filename = $_FILES['files']['name'][$key];
        $ext = strtolower(pathinfo($filename, PATHINFO_EXTENSION));
        
        if (!in_array($ext, ['ipynb', 'py'])) {
            echo $OUTPUT->notification("Archivo no permitido: $filename (solo .ipynb o .py)", 'notifyproblem');
            continue;
        }

        // Mover a directorio temporal
        $temp_file = $temp_dir . '/' . basename($filename);
        if (!move_uploaded_file($tmp_name, $temp_file)) {
            throw new Exception("Error al mover archivo subido: " . error_get_last()['message']);
        }

        try {
            $result = procesar_archivo($temp_file, $ext === 'py');
            
            $notas[] = $result['nota'];
            // $feedbacks[] = "<strong>Archivo:</strong> " . s($filename) . "\n" . $result['feedback'];
            $feedbacks[] = $result['feedback'];
            $archivos_subidos[] = $result['archivo'];
            
            // Mover a uploads final
            $final_path = $upload_dir . $result['archivo'];
            if (!rename($temp_file, $final_path)) {
                error_log("No se pudo mover a uploads: " . error_get_last()['message']);
            }
            
        } catch (Exception $e) {
            @unlink($temp_file);
            echo $OUTPUT->notification("Error procesando $filename: " . $e->getMessage(), 'error');
            continue;
        }
    }

    if (!empty($archivos_subidos)) {
        // Calcular nota promedio
        $nota_final = !empty($notas) ? array_sum($notas) / count($notas) : 0;
        
        // Formatear el feedback correctamente
        $feedback_combinado = "";
        foreach ($feedbacks as $index => $feedback) {
            $filename = $_FILES['files']['name'][$index];
            $feedback_combinado .= "<strong>Archivo: " . s($filename) . "</strong><br>";
            $feedback_combinado .= "<div style='background: #f8f9fa; padding: 10px; border-radius: 5px; margin: 5px 0;'>";
            $feedback_combinado .= nl2br(s($feedback)) . "</div><br>";
        }

        // Mostrar resultados
        echo $OUTPUT->notification("Archivos procesados correctamente", 'success');
        echo "<div class='alert alert-success'><strong>Nota promedio:</strong> " . round($nota_final, 2) . "</div>";
        echo "<details class='mt-3'><summary class='btn btn-secondary'>Ver feedback detallado</summary>";
        echo "<div class='p-3 mt-2 bg-light border rounded'>" . $feedback_combinado . "</div></details>";

        // Botón volver
        echo '<div class="mt-3">';
        echo html_writer::link(new moodle_url('/mod/autocorreccion/view.php', ['id' => $id]), 
            'Volver al historial de entregas', 
            ['class' => 'btn btn-secondary']);
        echo '</div>';

        // Guardar en la base de datos
        $record = new stdClass();
        $record->userid = $USER->id;
        $record->autocorreccionid = $cm->instance;
        $record->nota = $nota_final;
        $record->feedback = strip_tags($feedback_combinado); // Guardar sin HTML
        $record->files = json_encode($archivos_subidos);
        $record->timecreated = time();
        $record->timemodified = time();


        try {
            $DB->insert_record('autocorreccion_envios', $record);
            
            // Actualizar calificación en Moodle
            $grade_result = grade_update(
                'mod/autocorreccion',
                $course->id,
                'mod',
                'autocorreccion',
                $cm->instance,
                0,
                [
                    'userid' => $USER->id,
                    'rawgrade' => $nota_final,
                    'feedback' => $feedback_combinado,
                    'feedbackformat' => FORMAT_PLAIN
                ]
            );
            
            if ($grade_result !== GRADE_UPDATE_OK) {
                echo $OUTPUT->notification("La nota se guardó pero hubo un problema al actualizar el libro de calificaciones", 'notifyproblem');
            }
        } catch (Exception $e) {
            echo $OUTPUT->notification("Error al guardar en la base de datos: " . $e->getMessage(), 'error');
        }
    } else {
        echo $OUTPUT->notification("No se procesaron archivos válidos", 'notifyproblem');
    }

} catch (Exception $e) {
    echo $OUTPUT->notification("Error: " . $e->getMessage(), 'error');
}

// Limpiar directorio temporal
array_map('unlink', glob("$temp_dir/*"));
@rmdir($temp_dir);

echo $OUTPUT->footer();

// Función auxiliar para mensajes de error de upload
function get_upload_error_message($error_code) {
    $errors = [
        UPLOAD_ERR_INI_SIZE => 'El archivo excede el tamaño permitido',
        UPLOAD_ERR_FORM_SIZE => 'El archivo excede el tamaño permitido por el formulario',
        UPLOAD_ERR_PARTIAL => 'El archivo solo se subió parcialmente',
        UPLOAD_ERR_NO_FILE => 'No se subió ningún archivo',
        UPLOAD_ERR_NO_TMP_DIR => 'Falta el directorio temporal',
        UPLOAD_ERR_CANT_WRITE => 'No se pudo escribir el archivo en disco',
        UPLOAD_ERR_EXTENSION => 'Una extensión de PHP detuvo la subida',
    ];
    return $errors[$error_code] ?? 'Error desconocido al subir el archivo';
}
?>