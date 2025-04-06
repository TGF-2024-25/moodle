<?php
defined('MOODLE_INTERNAL') || die();

function autocorreccion_supports($feature) {
    switch($feature) {
        case FEATURE_MOD_INTRO: return true;
        case FEATURE_BACKUP_MOODLE2: return true;
        case FEATURE_SHOW_DESCRIPTION: return true;
        default: return null;
    }
}

function autocorreccion_add_instance($moduleinstance, $mform = null) {
    global $DB;
    $moduleinstance->timecreated = time();
    $moduleinstance->timemodified = time();
    return $DB->insert_record('autocorreccion', $moduleinstance);
}

function autocorreccion_update_instance($moduleinstance, $mform = null) {
    global $DB;
    $moduleinstance->timemodified = time();
    $moduleinstance->id = $moduleinstance->instance;
    return $DB->update_record('autocorreccion', $moduleinstance);
}
