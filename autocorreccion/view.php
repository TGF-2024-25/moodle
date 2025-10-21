<?php
require_once('../../config.php');
require_once(__DIR__ . '/lib.php');
require_login();

$id = required_param('id', PARAM_INT);
$userid = optional_param('userid', 0, PARAM_INT);
$cm = get_coursemodule_from_id('autocorreccion', $id, 0, false, MUST_EXIST);
$course = get_course($cm->course);
$context = context_module::instance($cm->id);
// Obtener la configuración de la actividad
$autocorreccion = $DB->get_record('autocorreccion', ['id' => $cm->instance]);

require_course_login($course, true, $cm);

$PAGE->set_context($context);
$PAGE->set_course($course);
$PAGE->set_cm($cm);

if (!autocorreccion_can_view_submissions($context) && !autocorreccion_can_submit($context)) {
    throw new required_capability_exception($context, 'mod/autocorreccion:view', 'nopermissions', '');
}

$PAGE->set_url('/mod/autocorreccion/view.php', ['id' => $id]);
$PAGE->set_title('Resultados de Corrección');
$PAGE->set_heading(format_string($course->fullname));

$PAGE->requires->css(new moodle_url('/mod/autocorreccion/style.css'));
$PAGE->add_body_class('mod-autocorreccion-container');

echo $OUTPUT->header();

// ========== VISTA PARA PROFESOR ==========
if (autocorreccion_is_teacher($context)) {
    echo html_writer::tag('h2', 'Listado de estudiantes');
    
    $sql_estudiantes = "SELECT DISTINCT u.id, u.firstname, u.lastname 
                       FROM {autocorreccion_envios} s
                       JOIN {user} u ON s.userid = u.id
                       WHERE s.autocorreccionid = ?
                       ORDER BY u.lastname ASC";
    $estudiantes = $DB->get_records_sql($sql_estudiantes, [$cm->instance]);
    
    if (!empty($estudiantes)) {
        echo html_writer::start_tag('ul', ['class' => 'lista-estudiantes']);
        foreach ($estudiantes as $est) {
            $url = new moodle_url('/mod/autocorreccion/view.php', [
                'id' => $id,
                'userid' => $est->id
            ]);
            echo html_writer::tag('li',
                html_writer::link($url, fullname($est), ['class' => 'estudiante-link'])
            );
        }
        echo html_writer::end_tag('ul');
    } else {
        echo $OUTPUT->notification('No hay entregas de estudiantes aún', 'notifyinfo');
    }
    
    if ($userid) {
        $estudiante = $DB->get_record('user', ['id' => $userid]);
        echo html_writer::tag('h3', 'Entregas de '.fullname($estudiante));
        
        $entregas = $DB->get_records('autocorreccion_envios', [
            'userid' => $userid,
            'autocorreccionid' => $cm->instance
        ], 'timecreated DESC');
        
        if (!empty($entregas)) {
            echo html_writer::start_tag('div', ['class' => 'stats-box']);
            echo html_writer::tag('h4', 'Estadísticas del estudiante');
            echo html_writer::start_tag('ul');

            $stats = [
                'Total entregas' => count($entregas),
                'Nota media' => array_reduce($entregas, function($carry, $item) {
                    return $carry + ($item->nota ?? 0);
                }, 0) / max(1, count($entregas)),
                'Mejor nota' => max(array_column($entregas, 'nota'))
            ];

            foreach ($stats as $label => $value) {
                echo html_writer::tag('li', 
                    html_writer::tag('strong', $label.': ') . round($value, 2));
            }

            echo html_writer::end_tag('ul');
            echo html_writer::end_tag('div');
            
            $table = new html_table();
            $table->head = [
                get_string('date'),
                get_string('files'),
                get_string('grade'),
                get_string('feedback'),
                'Acciones'
            ];
            $table->attributes['class'] = 'generaltable entregas-table';
            
            foreach ($entregas as $entrega) {
                $filelist = json_decode($entrega->files ?? '[]', true);
                $archivos = '';
                if (!empty($filelist)) {
                    foreach ($filelist as $file) {
                        if (!empty($file)) {
                            $fileurl = moodle_url::make_pluginfile_url(
                                $context->id,
                                'mod_autocorreccion',
                                'submission',
                                $entrega->id,
                                '/',
                                $file
                            );
                            $archivos .= html_writer::link($fileurl, s($file), 
                                ['target' => '_blank', 'class' => 'file-link']).'<br>';
                        }
                    }
                }
                
                // Feedback combinado (automático + profesor)
                $feedback_content = '';
                if (!empty($entrega->feedback)) {
                    $lineas_feedback = explode("\n", $entrega->feedback);
                    foreach ($lineas_feedback as $linea) {
                        if (trim($linea)) {
                            $feedback_content .= html_writer::tag('div', s($linea), ['class' => 'feedback-line']);
                        }
                    }
                }

                if (!empty($entrega->teacher_feedback)) {
                    if (!empty($feedback_content)) {
                        $feedback_content .= html_writer::empty_tag('br');
                    }
                    $feedback_content .= html_writer::tag('strong', 'Comentario profesor: ');
                    $feedback_content .= html_writer::tag('div', format_text($entrega->teacher_feedback, FORMAT_HTML), 
                        ['class' => 'teacher-feedback']);
                }

                $feedback_cell = $feedback_content;
                
                $editurl = new moodle_url('/mod/autocorreccion/editfeedback.php', [
                    'id' => $entrega->id,
                    'courseid' => $course->id
                ]);

                // Mostrar ambas notas (NbGrader y Rúbrica)
                $nota_cell = html_writer::tag('div', 'NbGrader: '.($entrega->nota ?? 'N/A'), [
                    'class' => ($entrega->nota >= 5 ? 'nota-alta' : 'nota-baja')
                ]);

                if (!empty($entrega->rubric_grade)) {
                    $rubric_class = autocorreccion_get_rubric_class($entrega->rubric_grade, $autocorreccion);
                    $nota_cell .= html_writer::tag('div', 'Rúbrica: '.$entrega->rubric_grade, [
                        'class' => 'rubric-grade ' . $rubric_class
                    ]);
                }

                $table->data[] = [
                    userdate($entrega->timecreated, get_string('strftimedatetime')),
                    $archivos ?: '-',
                    $nota_cell,
                    $feedback_cell,
                    $OUTPUT->action_icon($editurl, new pix_icon('i/edit', 'Editar'), null, [
                        'class' => 'btn-edit-feedback'
                    ])
                ];
            }
            
            echo html_writer::table($table);
        } else {
            echo $OUTPUT->notification('Este estudiante no tiene entregas aún', 'notifyinfo');
        }
    }
} 
// ========== VISTA PARA ESTUDIANTE ==========
else {
    if (autocorreccion_can_submit($context)) {
        echo html_writer::tag('h2', get_string('fileupload', 'autocorreccion'));
        echo html_writer::start_tag('form', [
            'action' => 'upload.php', 
            'method' => 'post',
            'enctype' => 'multipart/form-data',
            'class' => 'submission-form'
        ]);
        echo html_writer::empty_tag('input', [
            'type' => 'hidden',
            'name' => 'id', 
            'value' => $id
        ]);
        echo html_writer::tag('div', 
            html_writer::empty_tag('input', [
                'type' => 'file',
                'name' => 'files[]',
                'accept' => '.ipynb,.py',
                'required' => 'required',
                'multiple' => 'multiple'
            ]) . 
            html_writer::empty_tag('input', [
                'type' => 'submit',
                'value' => get_string('submit', 'autocorreccion'),
                'class' => 'btn btn-primary'
            ]),
            ['class' => 'form-group']
        );
        echo html_writer::end_tag('form');
    }

    $records = $DB->get_records('autocorreccion_envios', [
        'userid' => $USER->id,
        'autocorreccionid' => $cm->instance
    ], 'timecreated DESC');

    try {
        if (empty($records)) {
            echo $OUTPUT->notification(get_string('nosubmissions', 'autocorreccion'), 'notifyinfo');
            echo $OUTPUT->footer();
            exit;
        }

        $ultima = reset($records);
        echo html_writer::start_tag('div', ['class' => 'ultima-entrega-destacada']);
        echo html_writer::tag('h3', get_string('lastsubmission', 'autocorreccion'));
        
        $filelist = json_decode($ultima->files ?? '[]', true);
        $archivos = '';
        if (!empty($filelist)) {
            foreach ($filelist as $file) {
                if (!empty($file)) {
                    $fileurl = moodle_url::make_pluginfile_url(
                        $context->id,
                        'mod_autocorreccion',
                        'submission',
                        $ultima->id,
                        '/',
                        $file
                    );
                    $archivos .= html_writer::link($fileurl, s($file), 
                        ['target' => '_blank', 'class' => 'file-link']).'<br>';
                }
            }
        }

        $info_items = [
            get_string('date') => !empty($ultima->timecreated) ? userdate($ultima->timecreated, get_string('strftimedatetime')) : '-',
            get_string('files') => !empty($archivos) ? $archivos : get_string('nofiles', 'autocorreccion'),
            get_string('grade') => html_writer::tag('span', 
                isset($ultima->nota) ? $ultima->nota : 'N/A', 
                ['class' => (isset($ultima->nota) && $ultima->nota >= 5 ? 'nota-alta' : 'nota-baja')])
        ];
        
        if (!empty($ultima->rubric_grade)) {
            // Si es rúbrica apto/no apto, mostrar el texto en lugar del número
            if (!is_numeric($ultima->rubric_grade)) {
                $rubric_class = autocorreccion_get_rubric_class($ultima->rubric_grade, $autocorreccion);
                $info_items['Nota Rúbrica'] = html_writer::tag('span', 
                    $ultima->rubric_grade, 
                    ['class' => 'rubric-grade ' . $rubric_class]);
            } else {
                // Para rúbrica numérica, mostrar el número formateado
                $rubric_class = autocorreccion_get_rubric_class($ultima->rubric_grade, $autocorreccion);
                $info_items['Nota Rúbrica'] = html_writer::tag('span', 
                    number_format($ultima->rubric_grade, 2), 
                    ['class' => 'rubric-grade ' . $rubric_class]);
            }
        }

        foreach ($info_items as $label => $content) {
            if (empty($label) || empty($content)) continue;
            echo html_writer::start_tag('div', ['class' => 'info-item']);
            echo html_writer::tag('span', $label, ['class' => 'info-icon']);
            echo html_writer::tag('div', $content, ['class' => 'info-content']);
            echo html_writer::end_tag('div');
        }
        
        echo html_writer::start_tag('div', ['class' => 'feedback-container']);
        if (!empty($ultima->feedback)) {
            $lineas_feedback = explode("\n", $ultima->feedback);
            foreach ($lineas_feedback as $linea) {
                if (trim($linea)) {
                    echo html_writer::tag('div', s($linea), ['class' => 'feedback-line']);
                }
            }
        } else {
            echo get_string('nofeedback', 'autocorreccion');
        }
        
        if (!empty($ultima->teacher_feedback)) {
            echo html_writer::tag('h4', 'Comentario del profesor:', ['class' => 'teacher-feedback-title']);
            echo html_writer::tag('div', format_text($ultima->teacher_feedback, FORMAT_HTML), 
                ['class' => 'teacher-feedback-content']);
        }
        echo html_writer::end_tag('div');
        
        echo html_writer::end_tag('div');

        echo html_writer::start_tag('div', ['class' => 'stats-box']);
        echo html_writer::tag('h4', get_string('statistics', 'autocorreccion'));
        echo html_writer::start_tag('ul');

        $total_entregas = count($records);
        $nota_media = array_reduce($records, function($carry, $item) {
            return $carry + ($item->nota ?? 0);
        }, 0) / max(1, $total_entregas);
        $mejor_nota = max(array_column($records, 'nota'));

        $stat_items = [
            get_string('totalsubmissions', 'autocorreccion') => $total_entregas,
            get_string('averagegrade', 'autocorreccion') => round($nota_media, 2),
            get_string('bestgrade', 'autocorreccion') => round($mejor_nota, 2)
        ];

        foreach ($stat_items as $label => $value) {
            echo html_writer::tag('li', 
                html_writer::tag('strong', $label.': ') . $value);
        }

        echo html_writer::end_tag('ul');
        echo html_writer::end_tag('div');

        $historial = array_slice($records, 1);
        if (!empty($historial)) {
            echo html_writer::tag('h3', get_string('submissionhistory', 'autocorreccion'));
            $table = new html_table();
            $table->head = [
                get_string('date'),
                get_string('files'),
                get_string('grade'),
                get_string('feedback')
            ];
            $table->attributes['class'] = 'generaltable historial-table';
            
            foreach ($historial as $record) {
                $filelist = json_decode($record->files ?? '[]', true);
                $archivos = '';
                if (!empty($filelist)) {
                    foreach ($filelist as $file) {
                        if (!empty($file)) {
                            $fileurl = moodle_url::make_pluginfile_url(
                                $context->id,
                                'mod_autocorreccion',
                                'submission',
                                $record->id,
                                '/',
                                $file
                            );
                            $archivos .= html_writer::link($fileurl, s($file), 
                                ['target' => '_blank', 'class' => 'file-link']).'<br>';
                        }
                    }
                }
                
                // Feedback combinado para el historial
                $feedback_content = '';
                if (!empty($record->feedback)) {
                    $lineas_feedback = explode("\n", $record->feedback);
                    foreach ($lineas_feedback as $linea) {
                        if (trim($linea)) {
                            $feedback_content .= html_writer::tag('div', s($linea), ['class' => 'feedback-line']);
                        }
                    }
                }

                if (!empty($record->teacher_feedback)) {
                    if (!empty($feedback_content)) {
                        $feedback_content .= html_writer::empty_tag('br');
                    }
                    $feedback_content .= html_writer::tag('strong', 'Comentario profesor: ');
                    $feedback_content .= html_writer::tag('div', format_text($record->teacher_feedback, FORMAT_HTML), 
                        ['class' => 'teacher-feedback']);
                }

                $feedback_cell = $feedback_content;
                
                $table->data[] = [
                    userdate($record->timecreated, get_string('strftimedateshort')),
                    $archivos ?: '-',
                    html_writer::tag('span', 
                        $record->nota ?? 'N/A', 
                        ['class' => (($record->nota ?? 0) >= 5 ? 'nota-alta' : 'nota-baja')]),
                    $feedback_cell
                ];
            }
            
            echo html_writer::table($table);
        }
    } catch (Exception $e) {
        echo $OUTPUT->notification(get_string('unknownerror', 'autocorreccion'), 'error');
    }
}

echo $OUTPUT->footer();