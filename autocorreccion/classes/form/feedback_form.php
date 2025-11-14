<?php
defined('MOODLE_INTERNAL') || die();

require_once($CFG->libdir.'/formslib.php');

class mod_autocorreccion_feedback_form extends moodleform {
    protected function definition() {
        $mform = $this->_form;
        $submission = $this->_customdata['submission'];
        
        // Mostrar información del archivo
        $filelist = json_decode($submission->files ?? '[]', true);
        if (!empty($filelist)) {
            $files_html = '';
            foreach ($filelist as $file) {
                $files_html .= s($file).'<br>';
            }
            $mform->addElement('static', 'fileinfo', 'Archivo(s) enviado(s):', $files_html);
        }
        
        // Feedback automático de nbgrader (solo lectura)
        $autofeedback_html = $submission->feedback ?? '';

        if (!empty($autofeedback_html)) {
            // Si el feedback contiene HTML, lo mostramos renderizado
            $formatted_feedback = format_text($autofeedback_html, FORMAT_HTML);
        } else {
            $formatted_feedback = html_writer::tag('em', 'No hay feedback automático disponible.');
        }

        $mform->addElement('static', 'autofeedback_html', 'Feedback automático:', $formatted_feedback);
        
        // Feedback adicional del profesor
        $mform->addElement('editor', 'teacher_feedback', 'Comentario adicional', 
            ['rows' => 10]);
        $mform->setType('teacher_feedback', PARAM_RAW);
        
        // Campos ocultos
        $mform->addElement('hidden', 'id', $submission->id);
        $mform->setType('id', PARAM_INT);
        
        $mform->addElement('hidden', 'courseid');
        $mform->setType('courseid', PARAM_INT);
        
        $this->add_action_buttons();
        
        // Establecer datos iniciales
        $data = new stdClass();
        $data->id = $submission->id;
        $data->courseid = $this->_customdata['courseid'] ?? 0;
        $data->teacher_feedback = [
            'text' => $submission->teacher_feedback ?? '',
            'format' => FORMAT_HTML
        ];
        $this->set_data($data);
    }
}