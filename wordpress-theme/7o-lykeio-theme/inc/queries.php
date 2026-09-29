<?php
/**
 * Main query adjustments.
 *
 * @package lyk7
 */

defined( 'ABSPATH' ) || exit;

/**
 * Ordering, page sizes and document filters.
 *
 * @param WP_Query $q Query.
 */
function lyk7_pre_get_posts( $q ) {
	if ( is_admin() || ! $q->is_main_query() ) {
		return;
	}

	if ( $q->is_post_type_archive( 'anakoinosi' ) || $q->is_tax( 'kathgoria_anakoinosis' ) ) {
		$q->set( 'posts_per_page', 12 );
	}

	if ( $q->is_post_type_archive( 'drastiriotita' ) || $q->is_tax( 'eidos_drastiriotitas' ) ) {
		$q->set( 'posts_per_page', 12 );
		$q->set( 'meta_query', array( 'relation' => 'OR', 'ev' => array( 'key' => '_lyk7_event_date', 'compare' => 'EXISTS' ), array( 'key' => '_lyk7_event_date', 'compare' => 'NOT EXISTS' ) ) );
		$q->set( 'orderby', array( 'ev' => 'DESC', 'date' => 'DESC' ) );
	}

	if ( $q->is_post_type_archive( 'eggrafo' ) ) {
		// All documents on one page: the list is filtered live in the browser.
		$q->set( 'posts_per_page', -1 );

		$tax = array();
		// phpcs:disable WordPress.Security.NonceVerification.Recommended -- public filters.
		if ( ! empty( $_GET['eidos'] ) ) {
			$tax[] = array( 'taxonomy' => 'eidos_eggrafou', 'field' => 'slug', 'terms' => sanitize_title( wp_unslash( $_GET['eidos'] ) ) );
		}
		if ( ! empty( $_GET['etos'] ) ) {
			$tax[] = array( 'taxonomy' => 'sxoliko_etos', 'field' => 'slug', 'terms' => sanitize_title( wp_unslash( $_GET['etos'] ) ) );
		}
		// phpcs:enable
		if ( $tax ) {
			$q->set( 'tax_query', $tax );
		}
	}

	if ( $q->is_post_type_archive( 'gallery_item' ) ) {
		$q->set( 'posts_per_page', 48 );
		$q->set( 'orderby', array( 'menu_order' => 'ASC', 'date' => 'DESC' ) );
	}

	if ( $q->is_search() ) {
		$q->set( 'post_type', array( 'anakoinosi', 'drastiriotita', 'eggrafo', 'page' ) );
	}
}
add_action( 'pre_get_posts', 'lyk7_pre_get_posts' );

/**
 * A document has no page of its own: send visitors straight to the file.
 * Photos likewise open in the gallery.
 */
function lyk7_redirect_singles() {
	if ( is_singular( 'eggrafo' ) ) {
		$url = lyk7_doc_url( get_queried_object_id() );
		wp_safe_redirect( $url ? $url : get_post_type_archive_link( 'eggrafo' ), 302 );
		exit;
	}
	if ( is_singular( 'gallery_item' ) ) {
		wp_safe_redirect( get_post_type_archive_link( 'gallery_item' ), 302 );
		exit;
	}
}
add_action( 'template_redirect', 'lyk7_redirect_singles' );

/**
 * Allow redirects to external document links.
 *
 * @param string[] $hosts Hosts.
 * @return string[]
 */
function lyk7_allowed_redirect_hosts( $hosts ) {
	if ( is_singular( 'eggrafo' ) ) {
		$host = wp_parse_url( lyk7_doc_url( get_queried_object_id() ), PHP_URL_HOST );
		if ( $host ) {
			$hosts[] = $host;
		}
	}
	return $hosts;
}
add_filter( 'allowed_redirect_hosts', 'lyk7_allowed_redirect_hosts' );

/* ------------------------------------------------------------------ */
/* Self-healing URLs                                                    */
/* ------------------------------------------------------------------ */

/**
 * Mark every response that WordPress itself served, so the rewrite check
 * below can tell whether the web server routes pretty URLs to WordPress.
 */
function lyk7_marker_header() {
	if ( ! headers_sent() ) {
		header( 'X-Lyk7: 1' );
	}
}
add_action( 'after_setup_theme', 'lyk7_marker_header' );

/**
 * Check that a pretty URL actually reaches WordPress. On servers without
 * URL rewriting (no mod_rewrite / .htaccess) switch to /index.php/… links,
 * which work everywhere.
 */
function lyk7_check_rewrites() {
	$structure = (string) get_option( 'permalink_structure' );
	if ( '' === $structure || 0 === strpos( $structure, '/index.php' ) ) {
		return;
	}

	$url      = apply_filters( 'lyk7_rewrite_test_url', home_url( '/anakoinoseis/' ) );
	$response = wp_remote_get(
		$url,
		array(
			'timeout'     => 8,
			'redirection' => 0,
			'sslverify'   => false,
		)
	);

	if ( is_wp_error( $response ) ) {
		return; // Loopback blocked: cannot tell, leave as is.
	}

	if ( '' === (string) wp_remote_retrieve_header( $response, 'x-lyk7' ) ) {
		global $wp_rewrite;
		$wp_rewrite->set_permalink_structure( '/index.php/%postname%/' );
		update_option( 'lyk7_pathinfo_fallback', 1 );
		delete_option( 'lyk7_rewrite_version' );
	}
}

/**
 * Last line of defence: if one of the theme's URLs ends in a 404 (rules not
 * rebuilt yet, a conflicting page, a caching layer …), rebuild the rules and
 * send the visitor to the same content through a URL that always works.
 */
function lyk7_rescue_404() {
	if ( ! is_404() || ! empty( $_SERVER['QUERY_STRING'] ) ) {
		return;
	}

	$home = (string) wp_parse_url( home_url( '/' ), PHP_URL_PATH );
	$path = (string) wp_parse_url( isset( $_SERVER['REQUEST_URI'] ) ? wp_unslash( $_SERVER['REQUEST_URI'] ) : '', PHP_URL_PATH ); // phpcs:ignore WordPress.Security.ValidatedSanitizedInput
	$path = rawurldecode( $path );
	if ( $home && 0 === strpos( $path, $home ) ) {
		$path = substr( $path, strlen( $home ) );
	}
	$path  = preg_replace( '#^index\.php/?#', '', trim( $path, '/' ) );
	$parts = array_values( array_filter( explode( '/', $path ) ) );
	if ( ! $parts ) {
		return;
	}

	$archives = array(
		'anakoinoseis'  => 'anakoinosi',
		'zoi-scholeiou' => 'drastiriotita',
		'eggrafa'       => 'eggrafo',
		'stigmiotypa'   => 'gallery_item',
	);
	$terms    = array(
		'kathgoria'    => 'kathgoria_anakoinosis',
		'eidos-drasis' => 'eidos_drastiriotitas',
	);

	$target = '';
	$first  = sanitize_title( $parts[0] );

	if ( isset( $archives[ $first ] ) ) {
		$pt = $archives[ $first ];
		if ( 1 === count( $parts ) || 'page' === $parts[1] ) {
			$target = add_query_arg( 'post_type', $pt, home_url( '/' ) );
		} else {
			$id = lyk7_post_id_by_slug( sanitize_title( $parts[1] ), $pt );
			if ( $id ) {
				$target = add_query_arg( array( 'post_type' => $pt, 'p' => $id ), home_url( '/' ) );
			}
		}
	} elseif ( isset( $terms[ $first ] ) && isset( $parts[1] ) ) {
		$term = get_term_by( 'slug', sanitize_title( $parts[1] ), $terms[ $first ] );
		if ( $term ) {
			$target = add_query_arg( $terms[ $first ], $term->slug, home_url( '/' ) );
		}
	} else {
		$page = get_page_by_path( implode( '/', array_map( 'sanitize_title', $parts ) ) );
		if ( $page && 'publish' === $page->post_status ) {
			$target = add_query_arg( 'page_id', $page->ID, home_url( '/' ) );
		}
	}

	if ( ! $target ) {
		return;
	}

	// Rebuild the rules (at most every 10 minutes) so the next visit is clean.
	if ( ! get_transient( 'lyk7_rescue_flush' ) ) {
		set_transient( 'lyk7_rescue_flush', 1, 10 * MINUTE_IN_SECONDS );
		delete_option( 'lyk7_rewrite_version' );
	}

	wp_safe_redirect( $target, 302 );
	exit;
}
add_action( 'template_redirect', 'lyk7_rescue_404', 1 );
