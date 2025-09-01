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

        // Descripción
        $this->standard_intro_elements();

        // Botones estándar
        $this->standard_coursemodule_elements();
        $this->add_action_buttons();
    }
}
