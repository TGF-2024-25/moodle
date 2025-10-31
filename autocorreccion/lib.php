<?php
defined('MOODLE_INTERNAL') || die();

// Integración con el sistema de plugins de Moodle

function autocorreccion_supports($feature) {
    switch($feature) {
        case FEATURE_MOD_INTRO: return true;
        case FEATURE_BACKUP_MOODLE2: return true;
        case FEATURE_SHOW_DESCRIPTION: return true;
        case FEATURE_MOD_ARCHETYPE: return MOD_ARCHETYPE_OTHER;
        default: return null;
    }
}
function autocorreccion_add_instance($autocorreccion, $mform = null) {
    global $DB, $CFG;
    
    $autocorreccion->timemodified = time();
    
    // Insertar en la base de datos
    $autocorreccion->id = $DB->insert_record('autocorreccion', $autocorreccion);
    
    // Guardar archivo de referencia si existe
    if ($autocorreccion->id && isset($autocorreccion->reference_notebook)) {
        $context = context_module::instance($autocorreccion->coursemodule);
        file_save_draft_area_files($autocorreccion->reference_notebook, $context->id, 
            'mod_autocorreccion', 'reference_notebook', $autocorreccion->id, 
            array('subdirs' => 0, 'maxbytes' => $CFG->maxbytes, 'maxfiles' => 1));
    }
    
    return $autocorreccion->id;
}

function autocorreccion_update_instance($autocorreccion, $mform = null) {
    global $DB, $CFG;
    
    $autocorreccion->timemodified = time();
    $autocorreccion->id = $autocorreccion->instance;
    
    // Actualizar en la base de datos
    $result = $DB->update_record('autocorreccion', $autocorreccion);
    
    // Guardar archivo de referencia si existe
    if ($result && isset($autocorreccion->reference_notebook)) {
        $context = context_module::instance($autocorreccion->coursemodule);
        file_save_draft_area_files($autocorreccion->reference_notebook, $context->id, 
            'mod_autocorreccion', 'reference_notebook', $autocorreccion->id, 
            array('subdirs' => 0, 'maxbytes' => $CFG->maxbytes, 'maxfiles' => 1));
    }
    
    return $result;
}

function autocorreccion_delete_instance($id) {
    global $DB;
    
    if (!$autocorreccion = $DB->get_record('autocorreccion', array('id' => $id))) {
        return false;
    }
    
    // Eliminar archivos asociados
    $fs = get_file_storage();
    $context = context_module::instance($autocorreccion->coursemodule);
    $fs->delete_area_files($context->id, 'mod_autocorreccion', 'reference_notebook');
    
    // Eliminar envíos
    $DB->delete_records('autocorreccion_envios', array('autocorreccionid' => $id));
    
    // Eliminar actividad principal
    $DB->delete_records('autocorreccion', array('id' => $id));
    
    return true;
}

// Verifica si el usuario es profesor/gestor
function autocorreccion_is_teacher($context) {
    return has_any_capability([
        'mod/autocorreccion:manage',
        'mod/autocorreccion:viewallsubmissions'
    ], $context);
}

// Verifica permisos para ver entregas
function autocorreccion_can_view_submissions($context) {
    return has_capability('mod/autocorreccion:viewallsubmissions', $context) || 
           autocorreccion_is_teacher($context);
}

// Verifica permisos para enviar archivos
function autocorreccion_can_submit($context) {
    return has_capability('mod/autocorreccion:submit', $context);
}

function autocorreccion_grade_items($autocorreccion) {
    return [
        [
            'itemname' => clean_param($autocorreccion->name, PARAM_NOTAGS),
            'itemnumber' => 0,
            'gradetype' => GRADE_TYPE_VALUE,
            'grademax'  => 10,
            'grademin'  => 0,
        ]
    ];
}

function autocorreccion_get_coursemodule_info($coursemodule) {
    $info = new cached_cm_info();
    $info->name = $coursemodule->name;
    return $info;
}

function autocorreccion_get_extra_capabilities() {
    return [
        'moodle/course:view',
        'moodle/course:viewhiddenactivities',
        'mod/autocorreccion:view'
    ];
}

function autocorreccion_pluginfile($course, $cm, $context, $filearea, $args, $forcedownload, array $options=array()) {
    global $DB, $USER;
    
    if ($context->contextlevel != CONTEXT_MODULE) {
        return false;
    }

    require_login($course, true, $cm);

    if ($filearea === 'reference_notebook') {
        // Para notebooks de referencia - acceso simple para usuarios del curso
        $itemid = array_shift($args);
        $filename = array_pop($args);
        
        $fs = get_file_storage();
        $file = $fs->get_file($context->id, 'mod_autocorreccion', $filearea, $itemid, '/', $filename);
        
        if ($file) {
            send_stored_file($file, 0, 0, true, $options);
            return true;
        }
        return false;
        
    } elseif ($filearea === 'submission') {
        // Para entregas de estudiantes
        $itemid = array_shift($args);
        $filename = array_pop($args);
        
        if (!$submission = $DB->get_record('autocorreccion_envios', ['id' => $itemid])) {
            return false;
        }

        // Verificar permisos
        $can_view = ($submission->userid == $USER->id) || 
                   has_capability('mod/autocorreccion:viewallsubmissions', $context);
        
        if (!$can_view) {
            return false;
        }

        $fs = get_file_storage();
        $file = $fs->get_file($context->id, 'mod_autocorreccion', $filearea, $itemid, '/', $filename);
        
        if (!$file) {
            // Fallback a directorio uploads/
            $upload_dir = __DIR__ . "/uploads/";
            $filepath = $upload_dir . $filename;
            
            if (file_exists($filepath)) {
                header('Content-Description: File Transfer');
                header('Content-Type: application/octet-stream');
                header('Content-Disposition: attachment; filename="'.basename($filepath).'"');
                header('Expires: 0');
                header('Cache-Control: must-revalidate');
                header('Pragma: public');
                header('Content-Length: ' . filesize($filepath));
                readfile($filepath);
                exit;
            }
            return false;
        }

        send_stored_file($file, 0, 0, $forcedownload, $options);
        return true;
    }

    return false;
}

function autocorreccion_calculate_rubric_grade($nbgrader_grade, $autocorreccion) {
    if ($autocorreccion->rubric_type == 0) {
        // Rúbrica numérica: ajustar escala
        $max_nbgrader = !empty($autocorreccion->max_nbgrader_grade) ? 
            (float)$autocorreccion->max_nbgrader_grade : 10;
        
        if ($max_nbgrader > 0) {
            return ($nbgrader_grade / $max_nbgrader) * 10;
        }
        return $nbgrader_grade;
    } else {
        // Rúbrica apto/no apto
        $apto_threshold = !empty($autocorreccion->apto_threshold) ? 
            (float)$autocorreccion->apto_threshold : 6;
        $mejora_threshold = !empty($autocorreccion->mejora_threshold) ? 
            (float)$autocorreccion->mejora_threshold : 4;
        
        if ($nbgrader_grade >= $apto_threshold) {
            return 'Apto';
        } elseif ($nbgrader_grade >= $mejora_threshold) {
            return 'Necesita mejorar';
        } else {
            return 'No apto';
        }
    }
}

function autocorreccion_get_rubric_class($rubric_grade, $autocorreccion = null) {
    // Si no hay configuración específica, usar valores por defecto
    $apto_threshold = 6;
    $mejora_threshold = 4;
    
    // Usar valores configurados si están disponibles
    if ($autocorreccion) {
        if (isset($autocorreccion->apto_threshold)) {
            $apto_threshold = (float)$autocorreccion->apto_threshold;
        }
        if (isset($autocorreccion->mejora_threshold)) {
            $mejora_threshold = (float)$autocorreccion->mejora_threshold;
        }
    }
    
    if (is_numeric($rubric_grade)) {
        $numeric_grade = (float)$rubric_grade;
        
        if ($numeric_grade >= $apto_threshold) {
            return 'rubric-apto';
        } elseif ($numeric_grade >= $mejora_threshold) {
            return 'rubric-mejora';
        } else {
            return 'rubric-noapto';
        }
    } else {
        // Para calificaciones no numéricas (Apto/No Apto)
        if ($rubric_grade === 'Apto') {
            return 'rubric-apto';
        } elseif ($rubric_grade === 'Necesita mejorar') {
            return 'rubric-mejora';
        } else {
            return 'rubric-noapto';
        }
    }
}

function autocorreccion_process_reference_notebook($autocorreccion, $context) {
    // Procesar el notebook de referencia y prepararlo para NBGrader
    $fs = get_file_storage();
    $files = $fs->get_area_files($context->id, 'mod_autocorreccion', 'reference_notebook', 0);
    
    foreach ($files as $file) {
        if ($file->get_filename() != '.') {
            // Copiar a directorio de source de NBGrader
            $source_path = '/opt/nbgrader_course/source/' . $autocorreccion->assignment_name . '/' . $file->get_filename();
            $file->copy_content_to($source_path);
            
            // Generar assignment en NBGrader
            $command = "cd /opt/nbgrader_course && " .
                       "/opt/nbgrader_env/bin/nbgrader generate_assignment " . 
                       escapeshellarg($autocorreccion->assignment_name) . " --force 2>&1";
            exec($command, $output, $return_code);
            
            if ($return_code === 0) {
                return true;
            } else {
                error_log("Error generando assignment: " . implode("\n", $output));
                return false;
            }
        }
    }
    return false;
}