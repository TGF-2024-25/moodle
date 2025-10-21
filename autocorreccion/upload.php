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
$nbgrader_dir = "/opt/nbgrader_course";
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
    $command = "/opt/nbgrader_env/bin/python " . 
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
    
    // Nombre base del archivo
    $nombre_base = $USER->id . '_' . time() . '_' . basename($archivo);

    // Para archivos Python, convertimos primero a .ipynb
    if ($es_python) {
        $archivo_a_copiar = convertir_py_a_ipynb($archivo);
        $nombre_final_archivo = pathinfo($nombre_base, PATHINFO_FILENAME) . '.ipynb';
    } else {
        $archivo_a_copiar = $archivo;
        $nombre_final_archivo = $nombre_base;
    }

    // Calculamos la ruta de destino final
    $destino_final = $nbgrader_dir . '/submitted/' . $USER->username . '/ps1/' . $nombre_final_archivo;

    // Crear directorio de destino antes de copiar
    $directorio_destino = dirname($destino_final);
    if (!is_dir($directorio_destino)) {
        if (!mkdir($directorio_destino, 0777, true)) {
            throw new Exception('Error: No se pudo crear el directorio de destino para la corrección.');
        }
    }

    // Copiar archivo a NBGrader
    if (!copy($archivo_a_copiar, $destino_final)) {
        throw new Exception("Error al copiar el archivo a NBGrader: " . error_get_last()['message']);
    }

    chmod($destino_final, 0666);
    
    // Ejecutar NBGrader
    $command = "/opt/nbgrader_env/bin/python " .
               "/var/www/html/moodle/mod/autocorreccion/evaluate_nbgrader.py " .
               escapeshellarg($destino_final) . " " .
               escapeshellarg($USER->username) . " 2>&1";
    
    $output = shell_exec($command);
    // Limpiar posibles mensajes de debug antes del JSON
    $json_start = strpos($output, '{');
    if ($json_start !== false) {
        $output = substr($output, $json_start); // Tomar solo desde el inicio del JSON
    }

    $result = json_decode($output, true);

    if (!$result) {
        // Intentar limpiar más el output
        $output_limpio = preg_replace('/^[^{]*/', '', $output); // Eliminar todo antes del {
        $result = json_decode($output_limpio, true);
        
        if (!$result) {
            throw new Exception("La evaluación devolvió un formato inválido. Output: " . substr($output, 0, 200));
        }
    }
    
    return [
        'nota' => (float)$result['nota'],
        'feedback' => $result['retroalimentacion'],
        'archivo' => $nombre_final_archivo
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
                 get_upload_error_message($_FILES['files']['error'][$key]), 'notifyproblem');
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
            error_log("Resultado de procesar_archivo: " . print_r($result, true));     

            $notas[] = $result['nota'];
            $feedbacks[] = [
                'filename' => $filename,
                'feedback' => $result['feedback'],
                'saved_filename' => $result['archivo']
            ];
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

        // Calcular nota de rúbrica
        $autocorreccion = $DB->get_record('autocorreccion', ['id' => $cm->instance]);
        $rubric_grade = autocorreccion_calculate_rubric_grade($nota_final, $autocorreccion);
        
        // Formatear el feedback correctamente
        $feedback_combinado = "";
        foreach ($feedbacks as $item) {
            $feedback_combinado .= "Archivo: " . s($item['filename']) . "\n";
            
            // Procesar el feedback para mejor legibilidad
            $lineas = explode("\n", $item['feedback']);
            foreach ($lineas as $linea) {
                if (trim($linea)) {
                    $feedback_combinado .= $linea . "\n";
                }
            }
            $feedback_combinado .= "\n"; // Espacio entre archivos
        }

        // Mostrar resultados
        echo $OUTPUT->notification("Archivos procesados correctamente", 'success');
        echo "<div class='alert alert-success'><strong>Nota promedio:</strong> " . number_format($nota_final, 2) . "</div>";
        echo "<details class='mt-3'><summary class='btn btn-secondary'>Ver feedback detallado</summary>";
        echo "<div class='p-3 mt-2 bg-light border rounded'>" . nl2br(s($feedback_combinado)) . "</div></details>";

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
        $record->nota = round($nota_final, 2);
        $record->rubric_grade = is_numeric($rubric_grade) ? round($rubric_grade, 2) : $rubric_grade;
        $record->feedback = $feedback_combinado;
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