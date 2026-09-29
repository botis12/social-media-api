<?php
/**
 * One-click setup. Runs automatically when the theme is activated:
 *
 *  - pretty permalinks (/%postname%/) and a rewrite flush;
 *  - the pages (Το σχολείο μας, Μαθητές & Γονείς, Επικοινωνία …);
 *  - categories for announcements, activities and documents;
 *  - the four menus, assigned to their locations;
 *  - the site's current content (announcements, activities, documents,
 *    photos, logo) when the site has none yet.
 *
 * Safe to run again from Εμφάνιση → Εγκατάσταση θέματος: nothing is created twice.
 *
 * @package lyk7
 */

defined( 'ABSPATH' ) || exit;

/**
 * Run on activation.
 */
function lyk7_install_on_switch() {
	$has_content = (bool) get_posts( array( 'post_type' => 'anakoinosi', 'posts_per_page' => 1, 'post_status' => 'any', 'fields' => 'ids' ) );
	lyk7_install( ! $has_content );
}
add_action( 'after_switch_theme', 'lyk7_install_on_switch', 20 );

/**
 * Also run when the theme files were replaced in place (upload over the
 * active theme, FTP copy): WordPress does not fire after_switch_theme then.
 */
function lyk7_install_if_needed() {
	if ( get_option( 'lyk7_installed' ) === LYK7_VERSION || ! current_user_can( 'manage_options' ) || wp_doing_ajax() ) {
		return;
	}
	lyk7_install_on_switch();
}
add_action( 'admin_init', 'lyk7_install_if_needed' );

/**
 * Do the setup.
 *
 * @param bool $with_content Import the demo/current content too.
 * @return array Log lines.
 */
function lyk7_install( $with_content = true ) {
	$log  = array();
	$data = require LYK7_DIR . '/inc/demo-content.php';

	lyk7_register_content_types();

	// Site identity.
	if ( in_array( get_option( 'blogname' ), array( '', 'WordPress', 'My WordPress Website', 'My Blog' ), true ) ) {
		update_option( 'blogname', '7ο Γενικό Λύκειο Ιλίου' );
	}
	if ( in_array( get_option( 'blogdescription' ), array( '', 'Just another WordPress site' ), true ) ) {
		update_option( 'blogdescription', 'Βυτιβίλια 50-52, Ίλιον' );
	}
	if ( ! get_option( 'timezone_string' ) && ! (float) get_option( 'gmt_offset' ) ) {
		update_option( 'timezone_string', 'Europe/Athens' );
	}

	// Pretty permalinks — without them only the homepage works.
	if ( ! get_option( 'permalink_structure' ) ) {
		global $wp_rewrite;
		$wp_rewrite->set_permalink_structure( '/%postname%/' );
		$log[] = 'Ενεργοποιήθηκαν οι μόνιμοι σύνδεσμοι /%postname%/.';
	}

	// Pages.
	$page_ids = array();
	foreach ( $data['pages'] as $page ) {
		$path     = $page['parent'] ? $page['parent'] . '/' . $page['slug'] : $page['slug'];
		$existing = get_page_by_path( $path );
		if ( $existing ) {
			$page_ids[ $page['slug'] ] = $existing->ID;
			continue;
		}
		$page_ids[ $page['slug'] ] = wp_insert_post(
			array(
				'post_type'    => 'page',
				'post_status'  => 'publish',
				'post_title'   => $page['title'],
				'post_name'    => $page['slug'],
				'post_excerpt' => $page['excerpt'],
				'post_content' => $page['content'],
				'post_parent'  => $page['parent'] && isset( $page_ids[ $page['parent'] ] ) ? $page_ids[ $page['parent'] ] : 0,
			)
		);
		$log[] = 'Σελίδα: ' . $page['title'];
	}
	add_post_type_support( 'page', 'excerpt' );

	// Terms.
	foreach ( $data['ann_terms'] as $slug => $term ) {
		$id = lyk7_ensure_term( $term[0], $slug, 'kathgoria_anakoinosis' );
		if ( $id && ! get_term_meta( $id, 'lyk7_tone', true ) ) {
			update_term_meta( $id, 'lyk7_tone', $term[1] );
		}
	}
	foreach ( $data['act_terms'] as $slug => $name ) {
		lyk7_ensure_term( $name, $slug, 'eidos_drastiriotitas' );
	}
	foreach ( $data['doc_kinds'] as $slug => $name ) {
		lyk7_ensure_term( $name, $slug, 'eidos_eggrafou' );
	}

	if ( $with_content ) {
		$log = array_merge( $log, lyk7_import_content( $data ) );
	}

	lyk7_install_menus( $page_ids );
	$log[] = 'Δημιουργήθηκαν/ενημερώθηκαν τα μενού.';

	// Rules are rebuilt on wp_loaded (see lyk7_maybe_flush_rewrites).
	delete_option( 'lyk7_rewrite_version' );
	update_option( 'lyk7_installed', LYK7_VERSION );

	return $log;
}

/**
 * Create a term if missing.
 *
 * @param string $name     Name.
 * @param string $slug     Slug.
 * @param string $taxonomy Taxonomy.
 * @return int Term ID.
 */
function lyk7_ensure_term( $name, $slug, $taxonomy ) {
	$term = get_term_by( 'slug', $slug, $taxonomy );
	if ( $term ) {
		return (int) $term->term_id;
	}
	$res = wp_insert_term( $name, $taxonomy, array( 'slug' => $slug ) );
	return is_wp_error( $res ) ? 0 : (int) $res['term_id'];
}

/**
 * Copy a bundled file into the Media Library (once).
 *
 * @param string $rel   Path relative to assets/demo/.
 * @param string $title Title / alt.
 * @return int Attachment ID.
 */
function lyk7_import_media( $rel, $title = '' ) {
	static $cache = array();
	if ( isset( $cache[ $rel ] ) ) {
		return $cache[ $rel ];
	}

	$existing = get_posts(
		array(
			'post_type'      => 'attachment',
			'post_status'    => 'inherit',
			'posts_per_page' => 1,
			'fields'         => 'ids',
			'meta_key'       => '_lyk7_source',
			'meta_value'     => $rel,
		)
	);
	if ( $existing ) {
		$cache[ $rel ] = (int) $existing[0];
		return $cache[ $rel ];
	}

	$src = LYK7_DIR . '/assets/demo/' . $rel;
	if ( ! file_exists( $src ) ) {
		return 0;
	}

	require_once ABSPATH . 'wp-admin/includes/file.php';
	require_once ABSPATH . 'wp-admin/includes/media.php';
	require_once ABSPATH . 'wp-admin/includes/image.php';

	$tmp = wp_tempnam( basename( $src ) );
	copy( $src, $tmp );

	$id = media_handle_sideload(
		array(
			'name'     => basename( $src ),
			'tmp_name' => $tmp,
		),
		0,
		$title
	);

	if ( is_wp_error( $id ) ) {
		wp_delete_file( $tmp );
		return 0;
	}

	update_post_meta( $id, '_lyk7_source', $rel );
	if ( $title && wp_attachment_is_image( $id ) ) {
		update_post_meta( $id, '_wp_attachment_image_alt', $title );
	}

	$cache[ $rel ] = (int) $id;
	return $cache[ $rel ];
}

/**
 * Find a post of a type by slug.
 *
 * @param string $slug      Slug.
 * @param string $post_type Type.
 * @return int
 */
function lyk7_post_id_by_slug( $slug, $post_type ) {
	$found = get_posts(
		array(
			'name'           => $slug,
			'post_type'      => $post_type,
			'post_status'    => 'any',
			'posts_per_page' => 1,
			'fields'         => 'ids',
		)
	);
	return $found ? (int) $found[0] : 0;
}

/**
 * Import announcements, activities, documents, photos and the logo.
 *
 * @param array $data Content.
 * @return array Log.
 */
function lyk7_import_content( $data ) {
	$log = array();

	if ( ! has_custom_logo() ) {
		$logo = lyk7_import_media( 'logo-source.jpg', '7ο Γενικό Λύκειο Ιλίου' );
		if ( $logo ) {
			set_theme_mod( 'custom_logo', $logo );
		}
	}

	foreach ( $data['announcements'] as $a ) {
		if ( lyk7_post_id_by_slug( $a['slug'], 'anakoinosi' ) ) {
			continue;
		}
		$id = wp_insert_post(
			array(
				'post_type'    => 'anakoinosi',
				'post_status'  => 'publish',
				'post_title'   => $a['title'],
				'post_name'    => $a['slug'],
				'post_content' => $a['content'],
				'post_date'    => $a['date'],
			)
		);
		if ( ! $id || is_wp_error( $id ) ) {
			continue;
		}
		wp_set_object_terms( $id, $a['cat'], 'kathgoria_anakoinosis' );
		update_post_meta( $id, '_lyk7_urgent', $a['urgent'] ? 1 : 0 );
		update_post_meta( $id, '_lyk7_deadline', $a['deadline'] );
		if ( $a['image'] ) {
			set_post_thumbnail( $id, lyk7_import_media( $a['image'], $a['image_alt'] ) );
		}
	}
	$log[] = 'Ανακοινώσεις: ' . count( $data['announcements'] );

	foreach ( $data['activities'] as $a ) {
		if ( lyk7_post_id_by_slug( $a['slug'], 'drastiriotita' ) ) {
			continue;
		}
		$id = wp_insert_post(
			array(
				'post_type'    => 'drastiriotita',
				'post_status'  => 'publish',
				'post_title'   => $a['title'],
				'post_name'    => $a['slug'],
				'post_content' => $a['content'],
				'post_date'    => $a['date'],
			)
		);
		if ( ! $id || is_wp_error( $id ) ) {
			continue;
		}
		wp_set_object_terms( $id, $a['cat'], 'eidos_drastiriotitas' );
		update_post_meta( $id, '_lyk7_event_date', $a['event'] );
		update_post_meta( $id, '_lyk7_place', $a['place'] );
		if ( $a['image'] ) {
			set_post_thumbnail( $id, lyk7_import_media( $a['image'], $a['title'] ) );
		}
	}
	$log[] = 'Δραστηριότητες: ' . count( $data['activities'] );

	foreach ( $data['documents'] as $i => $doc ) {
		$slug = sanitize_title( pathinfo( $doc['file'], PATHINFO_FILENAME ) );
		if ( lyk7_post_id_by_slug( $slug, 'eggrafo' ) ) {
			continue;
		}
		$id = wp_insert_post(
			array(
				'post_type'   => 'eggrafo',
				'post_status' => 'publish',
				'post_title'  => $doc['title'],
				'post_name'   => $slug,
				'post_date'   => wp_date( 'Y-m-d H:i:s', time() - $i * HOUR_IN_SECONDS ),
			)
		);
		if ( ! $id || is_wp_error( $id ) ) {
			continue;
		}
		wp_set_object_terms( $id, $doc['kind'], 'eidos_eggrafou' );
		$year = lyk7_ensure_term( $doc['year'], $doc['year'], 'sxoliko_etos' );
		wp_set_object_terms( $id, array( $year ), 'sxoliko_etos' );
		update_post_meta( $id, '_lyk7_file_id', lyk7_import_media( 'docs/' . $doc['file'], $doc['title'] ) );
	}
	$log[] = 'Έγγραφα: ' . count( $data['documents'] ) . ' (δείγματα PDF — αντικαταστήστε τα με τα πραγματικά)';

	$existing_gallery = get_posts( array( 'post_type' => 'gallery_item', 'posts_per_page' => 1, 'post_status' => 'any', 'fields' => 'ids' ) );
	if ( ! $existing_gallery ) {
		foreach ( $data['gallery'] as $i => $g ) {
			$id = wp_insert_post(
				array(
					'post_type'   => 'gallery_item',
					'post_status' => 'publish',
					'post_title'  => $g['caption'],
					'menu_order'  => $i,
				)
			);
			if ( $id && ! is_wp_error( $id ) ) {
				set_post_thumbnail( $id, lyk7_import_media( $g['file'], $g['caption'] ) );
			}
		}
		$log[] = 'Φωτογραφίες: ' . count( $data['gallery'] );
	}

	return $log;
}

/**
 * Create the four menus (if missing) and assign them.
 *
 * @param int[] $page_ids Page IDs by slug.
 */
function lyk7_install_menus( $page_ids ) {
	$locations = get_theme_mod( 'nav_menu_locations', array() );

	$menus = array(
		'primary'         => 'Κύριο μενού',
		'footer-quick'    => 'Υποσέλιδο — Γρήγοροι σύνδεσμοι',
		'footer-external' => 'Υποσέλιδο — Χρήσιμοι σύνδεσμοι',
		'legal'           => 'Θεσμικά',
	);

	foreach ( $menus as $location => $name ) {
		if ( ! empty( $locations[ $location ] ) && wp_get_nav_menu_object( $locations[ $location ] ) ) {
			continue;
		}

		$menu = wp_get_nav_menu_object( $name );
		if ( $menu ) {
			$locations[ $location ] = $menu->term_id;
			continue;
		}

		$menu_id = wp_create_nav_menu( $name );
		if ( is_wp_error( $menu_id ) ) {
			continue;
		}
		$locations[ $location ] = $menu_id;

		if ( 'primary' === $location ) {
			$parent = lyk7_menu_page( $menu_id, $page_ids['to-scholeio-mas'] ?? 0 );
			if ( $parent ) {
				lyk7_menu_page( $menu_id, $page_ids['syllogos-didaskonton'] ?? 0, $parent );
				lyk7_menu_archive( $menu_id, 'gallery_item', 'Συλλογή Φωτογραφιών', $parent );
			}
			lyk7_menu_archive( $menu_id, 'anakoinosi', 'Ανακοινώσεις' );
			lyk7_menu_page( $menu_id, $page_ids['mathites-goneis'] ?? 0 );
			lyk7_menu_archive( $menu_id, 'drastiriotita', 'Ζωή του σχολείου' );
			lyk7_menu_archive( $menu_id, 'eggrafo', 'Έγγραφα' );
			lyk7_menu_page( $menu_id, $page_ids['epikoinonia'] ?? 0 );
		} elseif ( 'footer-quick' === $location ) {
			lyk7_menu_archive( $menu_id, 'anakoinosi', 'Ανακοινώσεις' );
			lyk7_menu_archive( $menu_id, 'eggrafo', 'Έγγραφα' );
			lyk7_menu_archive( $menu_id, 'drastiriotita', 'Ζωή του σχολείου' );
			lyk7_menu_archive( $menu_id, 'gallery_item', 'Συλλογή φωτογραφιών' );
		} elseif ( 'footer-external' === $location ) {
			foreach ( lyk7_default_links( 'footer-external' ) as $link ) {
				wp_update_nav_menu_item(
					$menu_id,
					0,
					array(
						'menu-item-title'  => $link[0],
						'menu-item-url'    => $link[1],
						'menu-item-type'   => 'custom',
						'menu-item-status' => 'publish',
						'menu-item-target' => '_blank',
					)
				);
			}
		} else {
			lyk7_menu_page( $menu_id, $page_ids['dilosi-prosvasimotitas'] ?? 0 );
			lyk7_menu_page( $menu_id, $page_ids['epikoinonia'] ?? 0 );
		}
	}

	set_theme_mod( 'nav_menu_locations', $locations );
}

/**
 * Add a page to a menu.
 *
 * @param int $menu_id Menu.
 * @param int $page_id Page.
 * @param int $parent  Parent menu item.
 * @return int Item ID.
 */
function lyk7_menu_page( $menu_id, $page_id, $parent = 0 ) {
	if ( ! $page_id ) {
		return 0;
	}
	$id = wp_update_nav_menu_item(
		$menu_id,
		0,
		array(
			'menu-item-object-id' => $page_id,
			'menu-item-object'    => 'page',
			'menu-item-type'      => 'post_type',
			'menu-item-parent-id' => $parent,
			'menu-item-status'    => 'publish',
		)
	);
	return is_wp_error( $id ) ? 0 : $id;
}

/**
 * Add a post type archive to a menu.
 *
 * @param int    $menu_id   Menu.
 * @param string $post_type Post type.
 * @param string $title     Label.
 * @param int    $parent    Parent item.
 * @return int
 */
function lyk7_menu_archive( $menu_id, $post_type, $title, $parent = 0 ) {
	$id = wp_update_nav_menu_item(
		$menu_id,
		0,
		array(
			'menu-item-title'     => $title,
			'menu-item-object'    => $post_type,
			'menu-item-type'      => 'post_type_archive',
			'menu-item-parent-id' => $parent,
			'menu-item-status'    => 'publish',
		)
	);
	return is_wp_error( $id ) ? 0 : $id;
}
