<?php
defined('MOODLE_INTERNAL') || die();

function xmldb_autocorreccion_upgrade($oldversion) {
    global $DB;
    $dbman = $DB->get_manager();

    if ($oldversion < 2025071601) {
        $table = new xmldb_table('autocorreccion_envios');
        
        $field = new xmldb_field('files', XMLDB_TYPE_TEXT, null, null, null, null, null, 'filename');
        if (!$dbman->field_exists($table, $field)) {
            $dbman->add_field($table, $field);
            
            $sql = "UPDATE {autocorreccion_envios} 
                    SET files = CONCAT('[\"', filename, '\"]') 
                    WHERE filename IS NOT NULL AND filename <> ''";
            $DB->execute($sql);
        }

        $fields_to_add = [
            ['teacherid', XMLDB_TYPE_INTEGER, '10', null, null, null, null, 'feedback'],
            ['timemodified', XMLDB_TYPE_INTEGER, '10', null, XMLDB_NOTNULL, null, '0', 'timecreated']
        ];
        
        foreach ($fields_to_add as $field_spec) {
            $field = new xmldb_field(...$field_spec);
            if (!$dbman->field_exists($table, $field)) {
                $dbman->add_field($table, $field);
            }
        }

        $DB->execute("UPDATE {autocorreccion_envios} SET timemodified = timecreated");

        $index = new xmldb_index('idx_user_activity', XMLDB_INDEX_NOTUNIQUE, ['userid', 'autocorreccionid']);
        if (!$dbman->index_exists($table, $index)) {
            $dbman->add_index($table, $index);
        }

        upgrade_plugin_savepoint(true, 2025071601, 'mod', 'autocorreccion');
    }

    if ($oldversion < 2025071602) {
        $table = new xmldb_table('autocorreccion_envios');
        $field = new xmldb_field('feedback', XMLDB_TYPE_TEXT, null, null, null, null, null);
        
        if ($dbman->field_exists($table, $field)) {
            $dbman->change_field_type($table, $field);
        }

        upgrade_plugin_savepoint(true, 2025071602, 'mod', 'autocorreccion');
    }

    // Nueva actualización para añadir teacher_feedback
    if ($oldversion < 2025072801) {
        $table = new xmldb_table('autocorreccion_envios');
        $field = new xmldb_field('teacher_feedback', XMLDB_TYPE_TEXT, null, null, null, null, null, 'feedback');
        
        if (!$dbman->field_exists($table, $field)) {
            $dbman->add_field($table, $field);
        }

        upgrade_plugin_savepoint(true, 2025072801, 'mod', 'autocorreccion');
    }

    return true;
}