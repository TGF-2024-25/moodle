<?php
require_once($CFG->dirroot.'/course/moodleform_mod.php');

// Define el formulario de configuración de la actividad

class mod_autocorreccion_mod_form extends moodleform_mod {
    public function definition() {
        global $CFG, $DB, $PAGE;

        $mform = $this->_form;

        // Título de la actividad
        $mform->addElement('text', 'name', get_string('name'), array('size' => '64'));
        $mform->setType('name', PARAM_TEXT);
        $mform->addRule('name', null, 'required', null, 'client');

        // Descripción
        $this->standard_intro_elements();

        // --- NUEVO: Notebook de referencia ---
        $mform->addElement('header', 'notebooksection', get_string('notebooksection', 'autocorreccion'));
        
        // Subir notebook de referencia
        $mform->addElement('filemanager', 'reference_notebook', 
            get_string('referencenotebook', 'autocorreccion'), 
            null, 
            array(
                'subdirs' => 0,
                'maxbytes' => $CFG->maxbytes,
                'maxfiles' => 1,
                'accepted_types' => array('.ipynb', 'py')
            )
        );
        
        // Nombre de la tarea en NBGrader
        $mform->addElement('text', 'assignment_name', get_string('assignmentname', 'autocorreccion'), array('size' => '20'));
        $mform->setType('assignment_name', PARAM_TEXT);
        $mform->setDefault('assignment_name', 'ps1');
        $mform->addRule('assignment_name', null, 'required', null, 'client');
        $mform->addHelpButton('assignment_name', 'assignmentname', 'autocorreccion');

        // --- Configuración de rúbrica ---
        $mform->addElement('header', 'rubrichdr', get_string('rubric_settings', 'autocorreccion'));

        $options = [
            0 => get_string('numeric_grade', 'autocorreccion'),
            1 => get_string('apto_noapto', 'autocorreccion')
        ];
        $mform->addElement('select', 'rubric_type', get_string('rubric_type', 'autocorreccion'), $options);
        $mform->setDefault('rubric_type', 0);

        // Configuración para rúbrica numérica
        $mform->addElement('text', 'max_nbgrader_grade', get_string('max_nbgrader_grade', 'autocorreccion'), array('size' => '5'));
        $mform->setType('max_nbgrader_grade', PARAM_FLOAT);
        $mform->setDefault('max_nbgrader_grade', 10);
        $mform->hideIf('max_nbgrader_grade', 'rubric_type', 'neq', 0);

        // Configuración para apto/no apto
        $mform->addElement('text', 'apto_threshold', get_string('apto_threshold', 'autocorreccion'), array('size' => '5'));
        $mform->setType('apto_threshold', PARAM_FLOAT);
        $mform->setDefault('apto_threshold', 6);
        $mform->hideIf('apto_threshold', 'rubric_type', 'neq', 1);

        $mform->addElement('text', 'mejora_threshold', get_string('mejora_threshold', 'autocorreccion'), array('size' => '5'));
        $mform->setType('mejora_threshold', PARAM_FLOAT);
        $mform->setDefault('mejora_threshold', 4);
        $mform->hideIf('mejora_threshold', 'rubric_type', 'neq', 1);

        // Botones estándar
        $this->standard_coursemodule_elements();
        $this->add_action_buttons();
    }

    public function data_preprocessing(&$default_values) {
        parent::data_preprocessing($default_values);
        
        // Preprocesar el filemanager para el notebook de referencia
        $draftitemid = file_get_submitted_draft_itemid('reference_notebook');
        file_prepare_draft_area($draftitemid, $this->context->id, 'mod_autocorreccion', 'reference_notebook', 
            !empty($default_values['id']) ? (int)$default_values['id'] : 0, 
            array('subdirs' => 0, 'maxbytes' => $CFG->maxbytes, 'maxfiles' => 1));
        $default_values['reference_notebook'] = $draftitemid;
    }

    public function validation($data, $files) {
        $errors = parent::validation($data, $files);
        
        // Validar nombre de assignment (solo letras, números y guiones bajos)
        if (!empty($data['assignment_name']) && !preg_match('/^[a-zA-Z0-9_]+$/', $data['assignment_name'])) {
            $errors['assignment_name'] = get_string('assignmentname_invalid', 'autocorreccion');
        }
        
        return $errors;
    }
}