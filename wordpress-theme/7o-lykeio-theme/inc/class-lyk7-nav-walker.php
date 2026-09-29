<?php
/**
 * Menu walker: submenu toggle buttons and external-link icons.
 *
 * @package lyk7
 */

defined( 'ABSPATH' ) || exit;

/**
 * Primary / footer menu walker.
 */
class Lyk7_Nav_Walker extends Walker_Nav_Menu {

	/**
	 * Start a submenu.
	 *
	 * @param string   $output Output.
	 * @param int      $depth  Depth.
	 * @param stdClass $args   Args.
	 */
	public function start_lvl( &$output, $depth = 0, $args = null ) {
		$output .= "\n<ul class=\"submenu\">\n";
	}

	/**
	 * Start an item.
	 *
	 * @param string   $output Output.
	 * @param WP_Post  $item   Item.
	 * @param int      $depth  Depth.
	 * @param stdClass $args   Args.
	 * @param int      $id     ID.
	 */
	public function start_el( &$output, $item, $depth = 0, $args = null, $id = 0 ) {
		$classes      = empty( $item->classes ) ? array() : (array) $item->classes;
		$has_children = in_array( 'menu-item-has-children', $classes, true );
		if ( $has_children && 0 === $depth ) {
			$classes[] = 'has-submenu';
		}

		$output .= '<li class="' . esc_attr( implode( ' ', array_filter( $classes ) ) ) . '">';

		$url      = (string) $item->url;
		$host     = wp_parse_url( home_url(), PHP_URL_HOST );
		$link_hst = wp_parse_url( $url, PHP_URL_HOST );
		$external = $link_hst && $link_hst !== $host;

		$atts = array(
			'class'        => 'menu-link',
			'href'         => $url,
			'aria-current' => $item->current ? 'page' : '',
			'target'       => $item->target ? $item->target : ( $external ? '_blank' : '' ),
			'rel'          => $external ? 'noopener noreferrer' : $item->xfn,
		);

		$attr_html = '';
		foreach ( $atts as $name => $value ) {
			if ( '' !== $value && null !== $value ) {
				$attr_html .= ' ' . $name . '="' . ( 'href' === $name ? esc_url( $value ) : esc_attr( $value ) ) . '"';
			}
		}

		$title   = apply_filters( 'the_title', $item->title, $item->ID );
		$output .= '<a' . $attr_html . '>' . esc_html( $title );
		if ( $external ) {
			$output .= ' ' . lyk7_get_icon( 'external', 14, 'menu-link__ext' );
		}
		$output .= '</a>';

		if ( $has_children && 0 === $depth ) {
			$output .= '<button type="button" class="submenu-toggle" aria-expanded="false" aria-label="' . esc_attr( 'Άνοιγμα υπομενού: ' . $title ) . '">' . lyk7_get_icon( 'arrow', 16 ) . '</button>';
		}
	}
}

/**
 * Fallback when no menu is assigned: the site's main sections.
 *
 * @param array $args Menu args.
 */
function lyk7_menu_fallback( $args ) {
	$links = lyk7_default_links( isset( $args['theme_location'] ) ? $args['theme_location'] : 'primary' );
	echo '<ul class="' . esc_attr( 'primary' === ( $args['theme_location'] ?? '' ) ? 'menu' : ( $args['menu_class'] ?? 'menu' ) ) . '">';
	foreach ( $links as $link ) {
		printf( '<li class="menu-item"><a class="menu-link" href="%s">%s</a></li>', esc_url( $link[1] ), esc_html( $link[0] ) );
	}
	echo '</ul>';
}

/**
 * Default links per menu location.
 *
 * @param string $location Location.
 * @return array[] [ label, url ]
 */
function lyk7_default_links( $location ) {
	$page = function ( $path ) {
		$p = get_page_by_path( $path );
		return $p ? get_permalink( $p ) : home_url( '/' . $path . '/' );
	};

	switch ( $location ) {
		case 'footer-quick':
			return array(
				array( 'Ανακοινώσεις', get_post_type_archive_link( 'anakoinosi' ) ),
				array( 'Έγγραφα', get_post_type_archive_link( 'eggrafo' ) ),
				array( 'Ζωή του σχολείου', get_post_type_archive_link( 'drastiriotita' ) ),
				array( 'Συλλογή φωτογραφιών', get_post_type_archive_link( 'gallery_item' ) ),
			);
		case 'footer-external':
			return array(
				array( 'Σύλλογος Καθηγητών', 'http://sylogos7oulykeioy.weebly.com/' ),
				array( 'Το Περιοδικό μας', 'http://schoolpress.sch.gr/7olykioiliou' ),
				array( 'Αποθετήριο Εργασιών', 'https://blogs.e-me.edu.gr/hive-axiologisiergasion2025-2026/' ),
				array( 'e-εγγραφές', 'https://e-eggrafes.minedu.gov.gr' ),
			);
		case 'legal':
			return array(
				array( 'Δήλωση Προσβασιμότητας', $page( 'dilosi-prosvasimotitas' ) ),
				array( 'Επικοινωνία', $page( 'epikoinonia' ) ),
			);
		default:
			return array(
				array( 'Το σχολείο μας', $page( 'to-scholeio-mas' ) ),
				array( 'Ανακοινώσεις', get_post_type_archive_link( 'anakoinosi' ) ),
				array( 'Μαθητές & Γονείς', $page( 'mathites-goneis' ) ),
				array( 'Ζωή του σχολείου', get_post_type_archive_link( 'drastiriotita' ) ),
				array( 'Έγγραφα', get_post_type_archive_link( 'eggrafo' ) ),
				array( 'Επικοινωνία', $page( 'epikoinonia' ) ),
			);
	}
}
