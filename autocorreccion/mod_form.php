<?php
require_once($CFG->dirroot.'/course/moodleform_mod.php');

// Define el formulario de configuración de la actividad

class mod_autocorreccion_mod_form extends moodleform_mod {
    public function definition() {
        $mform = $this->_form;

        // Título de la actividad
        $mform->addElement('text', 'name', get_string('name'), array('size' => '64'));
        $mform->setType('name', PARAM_TEXT);
        $mform->addRule('name', null, 'required', null, 'client');

        $mform->addElement('header', 'rubrichdr', get_string('rubric_settings', 'autocorreccion'));

        $options = [
            0 => get_string('numeric_grade', 'autocorreccion'),
            1 => get_string('apto_noapto', 'autocorreccion')
        ];
        $mform->addElement('select', 'rubric_type', get_string('rubric_type', 'autocorreccion'), $options);
        $mform->setDefault('rubric_type', 0);

        // Configuración para rúbrica numérica
        $mform->addElement('text', 'max_nbgrader_grade', get_string('max_nbgrader_grade', 'autocorreccion'));
        $mform->setType('max_nbgrader_grade', PARAM_FLOAT);
        $mform->setDefault('max_nbgrader_grade', 10);
        $mform->hideIf('max_nbgrader_grade', 'rubric_type', 'neq', 0);

        // Configuración para apto/no apto
        $mform->addElement('text', 'apto_threshold', get_string('apto_threshold', 'autocorreccion'));
        $mform->setType('apto_threshold', PARAM_FLOAT);
        $mform->setDefault('apto_threshold', 6);
        $mform->hideIf('apto_threshold', 'rubric_type', 'neq', 1);

        $mform->addElement('text', 'mejora_threshold', get_string('mejora_threshold', 'autocorreccion'));
        $mform->setType('mejora_threshold', PARAM_FLOAT);
        $mform->setDefault('mejora_threshold', 4);
        $mform->hideIf('mejora_threshold', 'rubric_type', 'neq', 1);

        // Descripción
        $this->standard_intro_elements();

        // Botones estándar
        $this->standard_coursemodule_elements();
        $this->add_action_buttons();
    }
}
