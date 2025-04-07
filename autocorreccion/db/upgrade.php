<?php
defined('MOODLE_INTERNAL') || die();

function xmldb_autocorreccion_upgrade($oldversion) {
    global $DB;

    // Verificar si la versión antigua es menor que la nueva versión (2025040700)
    if ($oldversion < 2025040700) {
        
        // Ejemplo: Añadir un campo nuevo a la tabla 'autocorreccion_envios'
        $table = new xmldb_table('autocorreccion_envios');

        // Comprobar si el campo 'autocorreccionid' no existe aún
        if (!$DB->get_manager()->field_exists($table, 'autocorreccionid')) {
            $field = new xmldb_field('autocorreccionid', XMLDB_TYPE_INTEGER, '10', null, XMLDB_NOTNULL, null, null, 'userid');
            $DB->get_manager()->add_field($table, $field);
        }

        // Marcar la actualización como completada
        upgrade_plugin_savepoint(true, 2025040700, 'mod', 'autocorreccion');
    }

    // Devolver true para indicar que la actualización fue exitosa
    return true;
}
?>