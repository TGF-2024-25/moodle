<?php
require_once('../../config.php');
require_login();
require_once($CFG->libdir.'/gradelib.php');
require_once(__DIR__ . '/lib.php');

$submissionid = required_param('id', PARAM_INT);
$courseid = required_param('courseid', PARAM_INT);

$submission = $DB->get_record('autocorreccion_envios', ['id' => $submissionid], '*', MUST_EXIST);
$cm = get_coursemodule_from_instance('autocorreccion', $submission->autocorreccionid, 0, false, MUST_EXIST);
$context = context_module::instance($cm->id);
require_capability('mod/autocorreccion:manage', $context);

$PAGE->set_url('/mod/autocorreccion/editfeedback.php', ['id' => $submissionid, 'courseid' => $courseid]);
$PAGE->set_title('Editar feedback');
$PAGE->set_heading('Editar retroalimentación');

require_once($CFG->dirroot.'/mod/autocorreccion/classes/form/feedback_form.php');
$mform = new mod_autocorreccion_feedback_form(null, [
    'submission' => $submission,
    'courseid' => $courseid
]);

if ($mform->is_cancelled()) {
    redirect(new moodle_url('/mod/autocorreccion/view.php', [
        'id' => $cm->id,
        'userid' => $submission->userid
    ]));
} else if ($data = $mform->get_data()) {
    // Procesar el feedback del profesor
    if (is_array($data->teacher_feedback)) {
        $teacher_feedback_text = $data->teacher_feedback['text'] ?? '';
    } else {
        $teacher_feedback_text = (string)$data->teacher_feedback;
    }
    
    // Actualizar solo el teacher_feedback
    $update_data = new stdClass();
    $update_data->id = $submissionid;
    $update_data->teacher_feedback = $teacher_feedback_text;
    $update_data->teacherid = $USER->id;
    $update_data->timemodified = time();
    
    $DB->update_record('autocorreccion_envios', $update_data);
    
    // Obtener la entrega completa y actualizada
    $current_submission = $DB->get_record('autocorreccion_envios', ['id' => $submissionid]);
    
    if ($current_submission) {
        // Preparar el feedback combinado para el gradebook
        $feedback_for_gradebook = '';
        
        // Feedback automático de NBGrader de esta entrega
        if (!empty($current_submission->feedback)) {
            $feedback_for_gradebook .= autocorreccion_format_feedback($current_submission->feedback);
        }
        
        // Feedback del profesor actualizado
        if (!empty($current_submission->teacher_feedback)) {
            if (!empty($feedback_for_gradebook)) {
                $feedback_for_gradebook .= "<hr style='margin: 10px 0;'>";
            }
            $feedback_for_gradebook .= html_writer::tag('div', 
                html_writer::tag('strong', 'Comentario del profesor:') . 
                html_writer::tag('div', format_text($current_submission->teacher_feedback, FORMAT_HTML)),
                ['class' => 'teacher-feedback-section']
            );
        }
        
        // Actualizar directamente el gradebook con el feedback combinado
        $grade_result = grade_update(
            'mod/autocorreccion',
            $courseid,
            'mod',
            'autocorreccion',
            $cm->instance,
            0,
            [
                'userid' => $current_submission->userid,
                'rawgrade' => $current_submission->nota,
                'feedback' => $feedback_for_gradebook,
                'feedbackformat' => FORMAT_HTML
            ]
        );
    }
    
    redirect(new moodle_url('/mod/autocorreccion/view.php', [
        'id' => $cm->id,
        'userid' => $current_submission->userid
    ]));
}

echo $OUTPUT->header();
$mform->display();
echo $OUTPUT->footer();