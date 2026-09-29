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
