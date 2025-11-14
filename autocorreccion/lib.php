<?php
defined('MOODLE_INTERNAL') || die();

// Integración con el sistema de plugins de Moodle

function autocorreccion_supports($feature) {
    switch($feature) {
        case FEATURE_MOD_INTRO: return true;
        case FEATURE_BACKUP_MOODLE2: return true;
        case FEATURE_SHOW_DESCRIPTION: return true;
        case FEATURE_MOD_ARCHETYPE: return MOD_ARCHETYPE_OTHER;
        case FEATURE_MOD_PURPOSE: return MOD_PURPOSE_ASSESSMENT;
        case FEATURE_COMMENT: return true;
        case FEATURE_GRADE_HAS_GRADE: return true;
        case FEATURE_GRADE_OUTCOMES: return false;
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
            'gradepass' => 5, // Nota para aprobar
        ]
    ];
}

function autocorreccion_get_coursemodule_info($coursemodule) {
    global $DB, $USER;
    
    $info = new cached_cm_info();
    $info->name = $coursemodule->name;
    
    // Obtener la actividad
    $autocorreccion = $DB->get_record('autocorreccion', ['id' => $coursemodule->instance]);
    if (!$autocorreccion) {
        return $info;
    }
    
    // Obtener la última entrega del usuario
    $sql = "SELECT * 
            FROM {autocorreccion_envios} 
            WHERE userid = ? AND autocorreccionid = ? 
            ORDER BY timecreated DESC 
            LIMIT 1";
    
    $submission = $DB->get_record_sql($sql, [$USER->id, $autocorreccion->id]);
    
    if ($submission) {
        // Feedback combinado del último envío
        $feedback_content = '';
        
        // Feedback automático de NBGrader
        if (!empty($submission->feedback)) {
            $feedback_content .= autocorreccion_format_feedback($submission->feedback);
        }
        
        // Feedback del profesor
        if (!empty($submission->teacher_feedback)) {
            if (!empty($feedback_content)) {
                $feedback_content .= "<hr style='margin: 10px 0;'>";
            }
            $feedback_content .= html_writer::tag('div', 
                html_writer::tag('strong', 'Comentario del profesor:') . 
                html_writer::tag('div', format_text($submission->teacher_feedback, FORMAT_HTML)),
                ['class' => 'teacher-feedback-section']
            );
        }
        
        if (!empty($feedback_content)) {
            $info->content = $feedback_content;
        }
        
        // Mostrar la nota
        if (isset($submission->nota)) {
            $info->customdata['grade'] = $submission->nota;
            if (!empty($submission->rubric_grade)) {
                $rubric_class = autocorreccion_get_rubric_class($submission->rubric_grade, $autocorreccion);
                $info->customdata['rubric_grade'] = $submission->rubric_grade;
                $info->customdata['rubric_class'] = $rubric_class;
            }
        }
    }
    
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

/**
 * Formatea feedback en HTML con las clases CSS adecuadas.
 *
 * @param string $raw_feedback Texto del feedback.
 * @param bool $multiple_archivos Si es cierto, añade separador entre archivos.
 * @return string HTML formateado.
 */
function autocorreccion_format_feedback($raw_feedback, $multiple_archivos = false) {
    $output = '';
    $feedbacks = explode("\n", trim($raw_feedback));
    $en_funciones = false;
    $tiene_resultados = false;

    foreach ($feedbacks as $linea) {
        $linea_limpia = trim($linea);
        if ($linea_limpia === '') continue;

        $clase_extra = '';
        $mostrar_linea = $linea_limpia;

        // Archivo
        if (stripos($linea_limpia, 'Archivo:') === 0) {
            $clase_extra = 'feedback-archivo';
            $en_funciones = false;

        // Resultados detallados
        } elseif (stripos($linea_limpia, 'RESULTADOS DETALLADOS') === 0 || strpos($linea_limpia, '===') !== false) {
            $clase_extra = 'feedback-header-detalles';
            $mostrar_linea = 'RESULTADOS DETALLADOS';
            $tiene_resultados = true;
            $en_funciones = true;

        // Nota final
        } elseif (stripos($linea_limpia, 'NOTA FINAL:') === 0) {
            $clase_extra = 'feedback-final-grade';
            $en_funciones = false;

        // Líneas de error - SOLO aplicar clase a la línea específica, no al contenedor
        } elseif (stripos($linea_limpia, 'Error:') !== false) {
            // NO aplicar $clase_extra = 'feedback-error' aquí
            if ($en_funciones) {
                $linea_limpia = preg_replace('/^[\s\-–•]+/', '', $linea_limpia);
                $mostrar_linea = '- ' . trim($linea_limpia);
                // Aplicar la clase SOLO al contenido de la función con error
                $clase_extra = 'feedback-error';
            }

        // Funciones de los resultados
        } elseif ($en_funciones) {
            $clase_extra = 'feedback-funcion';

            $linea_limpia = preg_replace('/^[\s\-–•]+/', '', $linea_limpia);
            $mostrar_linea = '- ' . trim($linea_limpia);

        // Si no hay resultados detallados
        } elseif (!$tiene_resultados && preg_match('/^[a-zA-Z_]+\s*:/', $linea_limpia)) {
            $output .= html_writer::tag('div', 'RESULTADOS DETALLADOS', [
                'class' => 'feedback-line feedback-header-detalles'
            ]);
            $clase_extra = 'feedback-funcion';
            $mostrar_linea = $linea_limpia;
            $tiene_resultados = true;
            $en_funciones = true;
        }

        $output .= html_writer::tag('div', $mostrar_linea, [
            'class' => 'feedback-line ' . $clase_extra
        ]);
    }

    if ($multiple_archivos) {
        $output .= html_writer::empty_tag('hr', ['class' => 'feedback-separator']);
    }

    return html_writer::tag('div', $output, ['class' => 'feedback-container']);
}

// Callback para mostrar el feedback en la página del curso
function autocorreccion_cm_info_view(cm_info $cm) {
    global $DB, $USER, $OUTPUT;
    
    $autocorreccion = $DB->get_record('autocorreccion', ['id' => $cm->instance]);
    if (!$autocorreccion) {
        return;
    }
    
    // Obtener la última entrega del usuario
    $submission = $DB->get_record('autocorreccion_envios', [
        'userid' => $USER->id,
        'autocorreccionid' => $autocorreccion->id
    ], '*', IGNORE_MULTIPLE);
    
    if (!$submission) {
        return;
    }
    
    $content = '';
    
    // Mostrar notas
    if (isset($submission->nota)) {
        $content .= html_writer::tag('div', 
            'Nota NBGrader: ' . $submission->nota, 
            ['class' => 'autocorreccion-grade']
        );
        
        if (!empty($submission->rubric_grade)) {
            $rubric_class = autocorreccion_get_rubric_class($submission->rubric_grade, $autocorreccion);
            $content .= html_writer::tag('div', 
                'Nota Rúbrica: ' . $submission->rubric_grade, 
                ['class' => 'autocorreccion-rubric-grade ' . $rubric_class]
            );
        }
    }
    
    // Feedback combinado, consistente con gradebook
    $feedback_content = '';
    
    // Feedback automático de NBGrader
    if (!empty($submission->feedback)) {
        $feedback_content .= autocorreccion_format_feedback($submission->feedback);
    }
    
    // Feedback del profesor
    if (!empty($submission->teacher_feedback)) {
        if (!empty($feedback_content)) {
            $feedback_content .= "<hr style='margin: 5px 0;'>";
        }
        $feedback_content .= html_writer::tag('div', 
            html_writer::tag('strong', 'Comentario del profesor: ') . 
            format_text($submission->teacher_feedback, FORMAT_HTML),
            ['class' => 'autocorreccion-teacher-feedback']
        );
    }
    
    if (!empty($feedback_content)) {
        $content .= html_writer::tag('div', $feedback_content, ['class' => 'autocorreccion-feedback-combined']);
    }
    
    if (!empty($content)) {
        $cm->set_after_edit_icons($content);
    }
}

// Registrar el callback para la página del curso
$callbacks = [
    'cm_info_view' => 'autocorreccion_cm_info_view'
];

// Callback para devolver información de calificación para el gradebook
function autocorreccion_get_user_grades($autocorreccion, $userid = 0) {
    global $DB;
    
    $grades = array();
    
    // Siempre obtener la última entrega
    if ($userid) {
        $sql = "SELECT * 
                FROM {autocorreccion_envios} 
                WHERE userid = ? AND autocorreccionid = ? 
                ORDER BY timecreated DESC 
                LIMIT 1";
        
        $submission = $DB->get_record_sql($sql, [$userid, $autocorreccion->id]);
    } else {
        // Para todos los usuarios
        $sql = "SELECT s1.* 
                FROM {autocorreccion_envios} s1 
                INNER JOIN (
                    SELECT userid, MAX(timecreated) as max_time 
                    FROM {autocorreccion_envios} 
                    WHERE autocorreccionid = ? 
                    GROUP BY userid
                ) s2 ON s1.userid = s2.userid AND s1.timecreated = s2.max_time 
                WHERE s1.autocorreccionid = ?";
        
        $submissions = $DB->get_records_sql($sql, [$autocorreccion->id, $autocorreccion->id]);
    }
    
    $submissions_to_process = $userid ? [$submission] : $submissions;
    
    foreach ($submissions_to_process as $submission) {
        if (!$submission) continue;
        
        $grade = new stdClass();
        $grade->userid = $submission->userid;
        $grade->rawgrade = $submission->nota;
        $grade->dategraded = $submission->timemodified;
        $grade->datesubmitted = $submission->timecreated;
        
        // Feedback combinado de la última entrega
        $feedback_content = '';
        
        // Feedback automático de NBGrader
        if (!empty($submission->feedback)) {
            $feedback_content .= autocorreccion_format_feedback($submission->feedback);
        }
        
        // Feedback del profesor
        if (!empty($submission->teacher_feedback)) {
            if (!empty($feedback_content)) {
                $feedback_content .= "<hr style='margin: 10px 0;'>";
            }
            $feedback_content .= html_writer::tag('div', 
                html_writer::tag('strong', 'Comentario del profesor:') . 
                html_writer::tag('div', format_text($submission->teacher_feedback, FORMAT_HTML)),
                ['class' => 'teacher-feedback-section']
            );
        }
        
        $grade->feedback = $feedback_content;
        $grade->feedbackformat = FORMAT_HTML;
        
        $grades[$grade->userid] = $grade;
    }
    
    return $grades;
}

function autocorreccion_grade_item_update($autocorreccion, $grades = null) {
    global $CFG, $DB;
    
    require_once($CFG->libdir . '/gradelib.php');
    
    $params = array('itemname' => $autocorreccion->name);
    
    if ($autocorreccion->grade > 0) {
        $params['gradetype'] = GRADE_TYPE_VALUE;
        $params['grademax']  = $autocorreccion->grade;
        $params['grademin']  = 0;
    } else {
        $params['gradetype'] = GRADE_TYPE_NONE;
    }
    
    if ($grades === 'reset') {
        $params['reset'] = true;
        $grades = null;
    }
    
    return grade_update('mod/autocorreccion', $autocorreccion->course, 'mod', 'autocorreccion', 
                       $autocorreccion->id, 0, $grades, $params);
}

// Actualiza las calificaciones en el gradebook
function autocorreccion_update_grades($autocorreccion, $userid = 0, $nullifnone = true) {
    global $CFG, $DB;
    
    require_once($CFG->libdir . '/gradelib.php');
    
    if ($grades = autocorreccion_get_user_grades($autocorreccion, $userid)) {
        autocorreccion_grade_item_update($autocorreccion, $grades);
    } else if ($userid && $nullifnone) {
        $grade = new stdClass();
        $grade->userid = $userid;
        $grade->rawgrade = null;
        autocorreccion_grade_item_update($autocorreccion, $grade);
    } else {
        autocorreccion_grade_item_update($autocorreccion);
    }
}