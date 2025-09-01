<?php
require_once('../../config.php');
require_login();
require_once($CFG->libdir.'/gradelib.php');

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
    // Actualizar el feedback del profesor
    $submission->teacher_feedback = $data->teacher_feedback['text'] ?? '';
    $submission->teacherid = $USER->id;
    $submission->timemodified = time();
    
    $DB->update_record('autocorreccion_envios', $submission);
    
    // Actualizar el libro de calificaciones
    $graderecord = [
        'userid' => $submission->userid,
        'feedback' => $submission->teacher_feedback,
        'feedbackformat' => FORMAT_HTML
    ];
    
    grade_update(
        'mod/autocorreccion',
        $courseid,
        'mod',
        'autocorreccion',
        $cm->instance,
        0,
        $graderecord
    );
    
    redirect(new moodle_url('/mod/autocorreccion/view.php', [
        'id' => $cm->id,
        'userid' => $submission->userid
    ]));
}

echo $OUTPUT->header();
$mform->display();
echo $OUTPUT->footer();