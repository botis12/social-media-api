<?php
/**
 * Content types and taxonomies.
 *
 *   anakoinosi     /anakoinoseis/   Ανακοινώσεις  + kathgoria_anakoinosis  /kathgoria/
 *   drastiriotita  /zoi-scholeiou/  Δραστηριότητες + eidos_drastiriotitas  /eidos-drasis/
 *   eggrafo        /eggrafa/        Έγγραφα        + eidos_eggrafou, sxoliko_etos (filters)
 *   gallery_item   /stigmiotypa/    Φωτογραφίες
 *
 * Rewrite rules are flushed automatically on activation and whenever the
 * theme version changes, so these URLs work without visiting Permalinks.
 *
 * @package lyk7
 */

defined( 'ABSPATH' ) || exit;

/**
 * Build the label set for a post type.
 *
 * @param string $plural   Plural.
 * @param string $singular Singular.
 * @param string $new      "Νέα …" form.
 * @return array
 */
function lyk7_pt_labels( $plural, $singular, $new ) {
	return array(
		'name'               => $plural,
		'singular_name'      => $singular,
		'menu_name'          => $plural,
		'add_new'            => 'Προσθήκη',
		'add_new_item'       => $new,
		'edit_item'          => 'Επεξεργασία: ' . $singular,
		'new_item'           => $new,
		'view_item'          => 'Προβολή',
		'view_items'         => 'Προβολή: ' . $plural,
		'search_items'       => 'Αναζήτηση',
		'not_found'          => 'Δεν βρέθηκαν εγγραφές.',
		'not_found_in_trash' => 'Δεν βρέθηκαν εγγραφές στα διαγραμμένα.',
		'all_items'          => 'Όλες/όλα',
		'archives'           => $plural,
		'featured_image'     => 'Εικόνα',
		'set_featured_image' => 'Ορισμός εικόνας',
	);
}

/**
 * Register the post types and taxonomies.
 */
function lyk7_register_content_types() {
	register_post_type(
		'anakoinosi',
		array(
			'labels'        => lyk7_pt_labels( 'Ανακοινώσεις', 'Ανακοίνωση', 'Νέα ανακοίνωση' ),
			'public'        => true,
			'show_in_rest'  => true,
			'menu_position' => 5,
			'menu_icon'     => 'dashicons-megaphone',
			'has_archive'   => 'anakoinoseis',
			'rewrite'       => array( 'slug' => 'anakoinoseis', 'with_front' => false ),
			'supports'      => array( 'title', 'editor', 'excerpt', 'thumbnail', 'revisions', 'author' ),
		)
	);

	register_post_type(
		'drastiriotita',
		array(
			'labels'        => lyk7_pt_labels( 'Δραστηριότητες', 'Δραστηριότητα', 'Νέα δραστηριότητα' ),
			'public'        => true,
			'show_in_rest'  => true,
			'menu_position' => 6,
			'menu_icon'     => 'dashicons-groups',
			'has_archive'   => 'zoi-scholeiou',
			'rewrite'       => array( 'slug' => 'zoi-scholeiou', 'with_front' => false ),
			'supports'      => array( 'title', 'editor', 'excerpt', 'thumbnail', 'revisions' ),
		)
	);

	register_post_type(
		'eggrafo',
		array(
			'labels'        => lyk7_pt_labels( 'Έγγραφα', 'Έγγραφο', 'Νέο έγγραφο' ),
			'public'        => true,
			'show_in_rest'  => true,
			'menu_position' => 7,
			'menu_icon'     => 'dashicons-media-document',
			'has_archive'   => 'eggrafa',
			'rewrite'       => array( 'slug' => 'eggrafa', 'with_front' => false ),
			'supports'      => array( 'title', 'excerpt', 'revisions' ),
		)
	);

	register_post_type(
		'gallery_item',
		array(
			'labels'        => lyk7_pt_labels( 'Φωτογραφίες', 'Φωτογραφία', 'Νέα φωτογραφία' ),
			'public'        => true,
			'show_in_rest'  => true,
			'menu_position' => 8,
			'menu_icon'     => 'dashicons-format-gallery',
			'has_archive'   => 'stigmiotypa',
			'rewrite'       => array( 'slug' => 'stigmiotypa', 'with_front' => false ),
			'supports'      => array( 'title', 'thumbnail', 'page-attributes' ),
		)
	);

	register_taxonomy(
		'kathgoria_anakoinosis',
		'anakoinosi',
		array(
			'labels'            => array(
				'name'          => 'Κατηγορίες ανακοινώσεων',
				'singular_name' => 'Κατηγορία ανακοίνωσης',
				'menu_name'     => 'Κατηγορίες',
				'add_new_item'  => 'Νέα κατηγορία',
				'edit_item'     => 'Επεξεργασία κατηγορίας',
				'all_items'     => 'Όλες οι κατηγορίες',
			),
			'hierarchical'      => true,
			'show_in_rest'      => true,
			'show_admin_column' => true,
			'rewrite'           => array( 'slug' => 'kathgoria', 'with_front' => false ),
		)
	);

	register_taxonomy(
		'eidos_drastiriotitas',
		'drastiriotita',
		array(
			'labels'            => array(
				'name'          => 'Είδη δράσης',
				'singular_name' => 'Είδος δράσης',
				'menu_name'     => 'Είδη δράσης',
				'add_new_item'  => 'Νέο είδος',
				'edit_item'     => 'Επεξεργασία είδους',
				'all_items'     => 'Όλα τα είδη',
			),
			'hierarchical'      => true,
			'show_in_rest'      => true,
			'show_admin_column' => true,
			'rewrite'           => array( 'slug' => 'eidos-drasis', 'with_front' => false ),
		)
	);

	// Document filters live on /eggrafa/?eidos=…&etos=… rather than on their own URLs.
	$filter_args = array(
		'hierarchical'       => true,
		'public'             => false,
		'publicly_queryable' => false,
		'show_ui'            => true,
		'show_in_rest'       => true,
		'show_admin_column'  => true,
		'query_var'          => false,
		'rewrite'            => false,
	);

	register_taxonomy(
		'eidos_eggrafou',
		'eggrafo',
		array_merge(
			$filter_args,
			array(
				'labels' => array(
					'name'          => 'Κατηγορίες εγγράφων',
					'singular_name' => 'Κατηγορία εγγράφου',
					'menu_name'     => 'Κατηγορίες',
					'add_new_item'  => 'Νέα κατηγορία',
					'edit_item'     => 'Επεξεργασία κατηγορίας',
				),
			)
		)
	);

	register_taxonomy(
		'sxoliko_etos',
		'eggrafo',
		array_merge(
			$filter_args,
			array(
				'labels' => array(
					'name'          => 'Σχολικά έτη',
					'singular_name' => 'Σχολικό έτος',
					'menu_name'     => 'Σχολικά έτη',
					'add_new_item'  => 'Νέο σχολικό έτος (π.χ. 2026-2027)',
					'edit_item'     => 'Επεξεργασία σχολικού έτους',
				),
			)
		)
	);

	$meta = array(
		'anakoinosi'    => array(
			'_lyk7_urgent'      => 'boolean',
			'_lyk7_deadline'    => 'string',
			'_lyk7_attachments' => 'string',
		),
		'drastiriotita' => array(
			'_lyk7_event_date' => 'string',
			'_lyk7_place'      => 'string',
		),
		'eggrafo'       => array(
			'_lyk7_file_id'  => 'integer',
			'_lyk7_file_url' => 'string',
		),
	);

	foreach ( $meta as $post_type => $fields ) {
		foreach ( $fields as $key => $type ) {
			register_post_meta(
				$post_type,
				$key,
				array(
					'type'          => $type,
					'single'        => true,
					'show_in_rest'  => true,
					'auth_callback' => function () {
						return current_user_can( 'edit_posts' );
					},
				)
			);
		}
	}

	register_term_meta(
		'kathgoria_anakoinosis',
		'lyk7_tone',
		array(
			'type'         => 'string',
			'single'       => true,
			'show_in_rest' => true,
		)
	);
}
add_action( 'init', 'lyk7_register_content_types' );

/**
 * Flush rewrite rules when the theme is activated.
 */
function lyk7_flush_on_switch() {
	// Flushed on wp_loaded, once everything (incl. the permalink structure) is in place.
	delete_option( 'lyk7_rewrite_version' );
}
add_action( 'after_switch_theme', 'lyk7_flush_on_switch' );

/**
 * Safety net: flush once after an update of the theme files, or if the
 * rules were lost (e.g. the theme was copied over FTP instead of activated).
 */
function lyk7_maybe_flush_rewrites() {
	if ( get_option( 'lyk7_rewrite_version' ) === LYK7_VERSION && get_option( 'rewrite_rules' ) ) {
		return;
	}

	global $wp_rewrite;
	$wp_rewrite->init();
	foreach ( array( 'anakoinosi', 'drastiriotita', 'eggrafo', 'gallery_item' ) as $pt ) {
		$obj = get_post_type_object( $pt );
		if ( $obj ) {
			$obj->add_rewrite_rules();
		}
	}
	foreach ( array( 'kathgoria_anakoinosis', 'eidos_drastiriotitas' ) as $tx ) {
		$obj = get_taxonomy( $tx );
		if ( $obj ) {
			$obj->add_rewrite_rules();
		}
	}
	flush_rewrite_rules();
	update_option( 'lyk7_rewrite_version', LYK7_VERSION );
}
add_action( 'wp_loaded', 'lyk7_maybe_flush_rewrites' );

/**
 * Colour tone of an announcement category: urgent or institutional.
 *
 * @param WP_Term|int $term Term.
 * @return string
 */
function lyk7_term_tone( $term ) {
	$term_id = is_object( $term ) ? $term->term_id : (int) $term;
	$tone    = get_term_meta( $term_id, 'lyk7_tone', true );

	return in_array( $tone, array( 'urgent', 'institutional', 'life' ), true ) ? $tone : 'institutional';
}

/**
 * Tone field on the category screens.
 *
 * @param WP_Term|string $term Term (edit screen) or taxonomy slug (add screen).
 */
function lyk7_tone_field( $term ) {
	$current = is_object( $term ) ? lyk7_term_tone( $term ) : 'institutional';
	$options = array(
		'institutional' => 'Μπλε — ενημερωτική',
		'urgent'        => 'Κεραμιδί — σημαντική / προθεσμίες',
		'life'          => 'Πράσινη — σχολική ζωή',
	);

	$select = '<select name="lyk7_tone" id="lyk7_tone">';
	foreach ( $options as $value => $label ) {
		$select .= sprintf( '<option value="%s"%s>%s</option>', esc_attr( $value ), selected( $current, $value, false ), esc_html( $label ) );
	}
	$select .= '</select>';

	wp_nonce_field( 'lyk7_tone', 'lyk7_tone_nonce' );

	if ( is_object( $term ) ) {
		printf( '<tr class="form-field"><th scope="row"><label for="lyk7_tone">Χρώμα ετικέτας</label></th><td>%s</td></tr>', $select ); // phpcs:ignore WordPress.Security.EscapeOutput
	} else {
		printf( '<div class="form-field"><label for="lyk7_tone">Χρώμα ετικέτας</label>%s</div>', $select ); // phpcs:ignore WordPress.Security.EscapeOutput
	}
}
add_action( 'kathgoria_anakoinosis_add_form_fields', 'lyk7_tone_field' );
add_action( 'kathgoria_anakoinosis_edit_form_fields', 'lyk7_tone_field' );

/**
 * Save the tone.
 *
 * @param int $term_id Term ID.
 */
function lyk7_save_tone( $term_id ) {
	if ( ! isset( $_POST['lyk7_tone_nonce'], $_POST['lyk7_tone'] ) || ! wp_verify_nonce( sanitize_key( $_POST['lyk7_tone_nonce'] ), 'lyk7_tone' ) ) {
		return;
	}
	update_term_meta( $term_id, 'lyk7_tone', sanitize_key( wp_unslash( $_POST['lyk7_tone'] ) ) );
}
add_action( 'created_kathgoria_anakoinosis', 'lyk7_save_tone' );
add_action( 'edited_kathgoria_anakoinosis', 'lyk7_save_tone' );
