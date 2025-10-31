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
    $command = "python3 " . 
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

function procesar_archivo($archivo, $es_python = false, $assignment_name = 'ps1') {
    global $USER, $temp_dir;
    
    // Nombre base del archivo
    $nombre_base = $USER->id . '_' . time() . '_' . basename($archivo);

    // Para archivos Python, convertimos primero a .ipynb
    if ($es_python) {
        $archivo_a_evaluar = convertir_py_a_ipynb($archivo);
        $nombre_final_archivo = pathinfo($nombre_base, PATHINFO_FILENAME) . '.ipynb';
    } else {
        $archivo_a_evaluar = $archivo;
        $nombre_final_archivo = $nombre_base;
    }

    // Usar API REST para evaluación externa
    $result = ejecutar_nbgrader_api($archivo_a_evaluar, $USER->username, $assignment_name);
    
    if (!$result || $result['estado'] === 'error') {
        throw new Exception("Error en evaluación NBGrader: " . ($result['error'] ?? 'Error desconocido'));
    }
    
    return [
        'nota' => (float)$result['nota'],
        'feedback' => $result['retroalimentacion'],
        'archivo' => $nombre_final_archivo
    ];
}

function ejecutar_nbgrader_api($notebook_path, $usuario, $assignment_name = 'ps1') {
    // Detectar automáticamente la IP del host
    $host_ip = detectar_ip_host();
    $api_url = "http://{$host_ip}:5000/grade";
    
    error_log("Conectando a API NBGrader en: $api_url");
    
    // Verificar que el archivo existe
    if (!file_exists($notebook_path)) {
        return [
            'estado' => 'error',
            'error' => "El archivo $notebook_path no existe"
        ];
    }
    
    // Preparar datos para la API usando CURLFile
    $post_data = [
        'notebook' => new CURLFile($notebook_path),
        'usuario' => $usuario,
        'assignment' => $assignment_name
    ];
    
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $api_url);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, $post_data);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_TIMEOUT, 60);
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'User-Agent: Moodle-AutoCorreccion/1.0'
    ]);
    
    $response = curl_exec($ch);
    $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $error = curl_error($ch);
    curl_close($ch);
    
    error_log("API NBGrader - HTTP Code: $http_code, Response: " . substr($response, 0, 200));
    
    if ($http_code !== 200) {
        return [
            'estado' => 'error',
            'error' => "Error HTTP $http_code en API NBGrader: " . ($error ?: $response)
        ];
    }
    
    $result = json_decode($response, true);
    
    if (json_last_error() !== JSON_ERROR_NONE) {
        return [
            'estado' => 'error',
            'error' => "Respuesta JSON inválida de la API: " . json_last_error_msg()
        ];
    }
    
    return $result;
}

function detectar_ip_host() {
    // Intentar diferentes métodos para detectar la IP del host
    $possible_ips = ['192.168.56.1', '10.0.2.2', 'localhost'];
    
    foreach ($possible_ips as $ip) {
        $test_url = "http://{$ip}:5000/health";
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $test_url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_TIMEOUT, 2);
        curl_setopt($ch, CURLOPT_NOBODY, true);
        
        if (curl_exec($ch) !== false) {
            $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
            curl_close($ch);
            if ($http_code == 200) {
                error_log("IP detectada para API: $ip");
                return $ip;
            }
        }
        curl_close($ch);
    }
    
    // Si no se detecta, usar la predeterminada
    error_log("No se pudo detectar IP del host, usando 192.168.56.1 por defecto");
    return '192.168.56.1';
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