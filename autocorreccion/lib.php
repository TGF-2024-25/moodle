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

function autocorreccion_delete_instance($id) {
    global $DB;

    // Elimina todos los envíos relacionados con esta instancia
    $DB->delete_records('autocorreccion_envios', ['autocorreccionid' => $id]);

    // Elimina la instancia principal
    return $DB->delete_records('autocorreccion', ['id' => $id]);
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
    global $DB;
    
    if ($context->contextlevel != CONTEXT_MODULE) {
        return false;
    }

    require_login($course, true, $cm);

    if ($filearea !== 'submission') {
        return false;
    }

    $itemid = array_shift($args);
    $filename = array_pop($args);
    
    if (!$submission = $DB->get_record('autocorreccion_envios', ['id' => $itemid])) {
        return false;
    }

    $fs = get_file_storage();
    $file = $fs->get_file($context->id, 'mod_autocorreccion', $filearea, $itemid, '/', $filename);
    
    if (!$file) {
        // Si el archivo no está en el sistema de archivos, intentar desde uploads/
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
}