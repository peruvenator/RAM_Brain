<?php
/**
 * Plugin Name: RSV Portfolio Storage
 * Description: Saves Return Stacked Visualizer portfolios per user in a custom database table.
 * Version:     1.0.0
 * Author:      Return Stacked
 */

defined( 'ABSPATH' ) || exit;

// ---------------------------------------------------------------------------
// Enqueue CDN dependencies on pages that use the widget
// Chart.js, its annotation plugin, and jsPDF must load in <head> – not inside
// a Divi Code module where Divi's HTML processing can mangle large script blocks.
// ---------------------------------------------------------------------------

add_action( 'wp_enqueue_scripts', 'rsv_enqueue_scripts' );

function rsv_enqueue_scripts() {
    // Only enqueue when the widget shortcode is present on this page
    global $post;
    if ( ! is_a( $post, 'WP_Post' ) || ! has_shortcode( $post->post_content, 'rsv_widget' ) ) {
        return;
    }

    wp_enqueue_script(
        'chartjs',
        'https://cdn.jsdelivr.net/npm/chart.js@4',
        [],
        null,
        false  // load in <head> so it's ready before the inline widget HTML parses
    );
    wp_enqueue_script(
        'chartjs-annotation',
        'https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation@3',
        [ 'chartjs' ],
        null,
        false
    );
    wp_enqueue_script(
        'jspdf',
        'https://cdn.jsdelivr.net/npm/jspdf@2/dist/jspdf.umd.min.js',
        [],
        null,
        false
    );
    wp_enqueue_style(
        'dm-sans',
        'https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap',
        [],
        null
    );
}

// ---------------------------------------------------------------------------
// Table creation on plugin activation
// ---------------------------------------------------------------------------

register_activation_hook( __FILE__, 'rsv_create_table' );

function rsv_create_table() {
    global $wpdb;
    $table   = $wpdb->prefix . 'rsv_portfolios';
    $charset = $wpdb->get_charset_collate();

    $sql = "CREATE TABLE IF NOT EXISTS {$table} (
        id         BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
        user_id    BIGINT UNSIGNED NOT NULL,
        name       VARCHAR(255)    NOT NULL,
        data       LONGTEXT        NOT NULL,
        created_at DATETIME        DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME        DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        INDEX idx_user_id (user_id)
    ) {$charset};";

    require_once ABSPATH . 'wp-admin/includes/upgrade.php';
    dbDelta( $sql );
}

// ---------------------------------------------------------------------------
// REST API routes
// ---------------------------------------------------------------------------

add_action( 'rest_api_init', 'rsv_register_routes' );

function rsv_register_routes() {
    register_rest_route( 'rsv/v1', '/portfolios', [
        [
            'methods'             => 'GET',
            'callback'            => 'rsv_list_portfolios',
            'permission_callback' => 'rsv_require_login',
        ],
        [
            'methods'             => 'POST',
            'callback'            => 'rsv_create_portfolio',
            'permission_callback' => 'rsv_require_login',
        ],
    ] );

    register_rest_route( 'rsv/v1', '/portfolios/(?P<id>\d+)', [
        [
            'methods'             => 'GET',
            'callback'            => 'rsv_get_portfolio',
            'permission_callback' => 'rsv_require_login',
        ],
        [
            'methods'             => 'PUT',
            'callback'            => 'rsv_update_portfolio',
            'permission_callback' => 'rsv_require_login',
        ],
        [
            'methods'             => 'DELETE',
            'callback'            => 'rsv_delete_portfolio',
            'permission_callback' => 'rsv_require_login',
        ],
    ] );
}

function rsv_require_login() {
    return is_user_logged_in();
}

// ---------------------------------------------------------------------------
// Handlers
// ---------------------------------------------------------------------------

/**
 * GET /rsv/v1/portfolios
 * Returns id + name + updated_at for all portfolios belonging to the current user.
 * Does NOT return the full data blob — keeps the list request small.
 */
function rsv_list_portfolios( WP_REST_Request $request ) {
    global $wpdb;
    $table   = $wpdb->prefix . 'rsv_portfolios';
    $user_id = get_current_user_id();

    $rows = $wpdb->get_results( $wpdb->prepare(
        "SELECT id, name, updated_at FROM {$table} WHERE user_id = %d ORDER BY updated_at DESC",
        $user_id
    ) );

    return rest_ensure_response( $rows );
}

/**
 * GET /rsv/v1/portfolios/{id}
 * Returns the full portfolio including the data blob.
 */
function rsv_get_portfolio( WP_REST_Request $request ) {
    global $wpdb;
    $table   = $wpdb->prefix . 'rsv_portfolios';
    $user_id = get_current_user_id();

    $row = $wpdb->get_row( $wpdb->prepare(
        "SELECT * FROM {$table} WHERE id = %d AND user_id = %d",
        $request['id'],
        $user_id
    ) );

    if ( ! $row ) {
        return new WP_Error( 'not_found', 'Portfolio not found.', [ 'status' => 404 ] );
    }

    $row->data = json_decode( $row->data );
    return rest_ensure_response( $row );
}

/**
 * POST /rsv/v1/portfolios
 * Body: { name: string, data: object }
 * Creates a new portfolio and returns { id, name }.
 */
function rsv_create_portfolio( WP_REST_Request $request ) {
    global $wpdb;
    $table   = $wpdb->prefix . 'rsv_portfolios';
    $user_id = get_current_user_id();

    $name = sanitize_text_field( $request->get_param( 'name' ) );
    $data = $request->get_param( 'data' );

    if ( ! $name || ! $data ) {
        return new WP_Error( 'bad_request', 'name and data are required.', [ 'status' => 400 ] );
    }

    $wpdb->insert( $table, [
        'user_id' => $user_id,
        'name'    => $name,
        'data'    => wp_json_encode( $data ),
    ] );

    return rest_ensure_response( [ 'id' => (int) $wpdb->insert_id, 'name' => $name ] );
}

/**
 * PUT /rsv/v1/portfolios/{id}
 * Body: { name?: string, data?: object }
 * Updates an existing portfolio (partial update supported).
 */
function rsv_update_portfolio( WP_REST_Request $request ) {
    global $wpdb;
    $table   = $wpdb->prefix . 'rsv_portfolios';
    $user_id = get_current_user_id();

    $exists = $wpdb->get_var( $wpdb->prepare(
        "SELECT id FROM {$table} WHERE id = %d AND user_id = %d",
        $request['id'],
        $user_id
    ) );

    if ( ! $exists ) {
        return new WP_Error( 'not_found', 'Portfolio not found.', [ 'status' => 404 ] );
    }

    $updates = [ 'updated_at' => current_time( 'mysql' ) ];

    if ( $request->get_param( 'name' ) ) {
        $updates['name'] = sanitize_text_field( $request->get_param( 'name' ) );
    }
    if ( $request->get_param( 'data' ) ) {
        $updates['data'] = wp_json_encode( $request->get_param( 'data' ) );
    }

    $wpdb->update( $table, $updates, [ 'id' => (int) $request['id'], 'user_id' => $user_id ] );

    return rest_ensure_response( [ 'id' => (int) $request['id'] ] );
}

/**
 * DELETE /rsv/v1/portfolios/{id}
 */
function rsv_delete_portfolio( WP_REST_Request $request ) {
    global $wpdb;
    $table   = $wpdb->prefix . 'rsv_portfolios';
    $user_id = get_current_user_id();

    $deleted = $wpdb->delete( $table, [ 'id' => (int) $request['id'], 'user_id' => $user_id ] );

    if ( ! $deleted ) {
        return new WP_Error( 'not_found', 'Portfolio not found.', [ 'status' => 404 ] );
    }

    return rest_ensure_response( [ 'deleted' => true ] );
}

// ---------------------------------------------------------------------------
// Shortcode: [rsv_widget]
// Renders the widget and injects the API config the JS needs.
// Usage in Divi: add a Code module with [rsv_widget]
// ---------------------------------------------------------------------------

add_shortcode( 'rsv_widget', 'rsv_widget_shortcode' );

function rsv_widget_shortcode( $atts ) {
    $api_base    = esc_url( rest_url( 'rsv/v1' ) );
    $nonce       = wp_create_nonce( 'wp_rest' );

    // rsv_widget_embed.html is the deploy-ready file produced by build_widget.py.
    // It contains no <!DOCTYPE>/html/head/body wrapper — just the widget div, CSS, and
    // a <script src="rsv_widget.js"> reference. Safe to return as shortcode content.
    $widget_path = plugin_dir_path( __FILE__ ) . 'rsv_widget_embed.html';

    if ( ! file_exists( $widget_path ) ) {
        return '<p>Widget embed file not found (rsv_widget_embed.html). Run build_widget.py and upload the file to the plugin directory.</p>';
    }

    $user       = wp_get_current_user();
    $user_email = esc_js( $user->user_email );
    $first_name = esc_js( get_user_meta( $user->ID, 'first_name', true ) );
    $last_name  = esc_js( get_user_meta( $user->ID, 'last_name',  true ) );

    $widget_html = file_get_contents( $widget_path );

    // Inject RSV_CONFIG immediately before the <script src="rsv_widget.js"> tag so
    // the global is defined before the JS file executes (the IIFE reads it at parse time).
    $config_script = "<script>
window.RSV_CONFIG = {
  apiBase:   '{$api_base}',
  nonce:     '{$nonce}',
  userEmail: '{$user_email}',
  firstName: '{$first_name}',
  lastName:  '{$last_name}'
};
</script>
";

    $widget_html = str_replace(
        '<script src=',
        $config_script . '<script src=',
        $widget_html
    );

    return $widget_html;
}
