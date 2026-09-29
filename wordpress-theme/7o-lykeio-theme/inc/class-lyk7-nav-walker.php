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

/**
 * Render a navigation area.
 *
 * By default the theme draws its own navigation, so every link works right
 * after activation whatever menus the site already had. Tick
 * «Χρήση των μενού του WordPress» in the Customizer to manage menus by hand.
 *
 * @param string $location Location.
 * @param string $class    List class.
 */
function lyk7_nav( $location, $class ) {
	if ( get_theme_mod( 'lyk7_use_wp_menus' ) && has_nav_menu( $location ) ) {
		wp_nav_menu(
			array(
				'theme_location' => $location,
				'container'      => false,
				'menu_class'     => $class,
				'depth'          => 'primary' === $location ? 2 : 1,
				'walker'         => new Lyk7_Nav_Walker(),
			)
		);
		return;
	}

	$items = lyk7_builtin_nav( $location );

	echo '<ul class="' . esc_attr( $class ) . '">';
	foreach ( $items as $item ) {
		$children = isset( $item[2] ) ? $item[2] : array();
		$current  = lyk7_is_current( $item[1] );
		$active   = $current;
		foreach ( $children as $child ) {
			$active = $active || lyk7_is_current( $child[1] );
		}

		$classes = array( 'menu-item' );
		if ( $children ) {
			$classes[] = 'menu-item-has-children';
			$classes[] = 'has-submenu';
		}
		if ( $current ) {
			$classes[] = 'current-menu-item';
		} elseif ( $active ) {
			$classes[] = 'current-menu-ancestor';
		}

		echo '<li class="' . esc_attr( implode( ' ', $classes ) ) . '">';
		lyk7_nav_link( $item[0], $item[1], $current );

		if ( $children ) {
			echo '<button type="button" class="submenu-toggle" aria-expanded="false" aria-label="' . esc_attr( 'Άνοιγμα υπομενού: ' . $item[0] ) . '">' . lyk7_get_icon( 'arrow', 16 ) . '</button>'; // phpcs:ignore WordPress.Security.EscapeOutput
			echo '<ul class="submenu">';
			foreach ( $children as $child ) {
				$c = lyk7_is_current( $child[1] );
				echo '<li class="menu-item' . ( $c ? ' current-menu-item' : '' ) . '">';
				lyk7_nav_link( $child[0], $child[1], $c );
				echo '</li>';
			}
			echo '</ul>';
		}
		echo '</li>';
	}
	echo '</ul>';
}

/**
 * One link, with the external-link icon for other sites.
 *
 * @param string $label   Label.
 * @param string $url     URL.
 * @param bool   $current Current page.
 */
function lyk7_nav_link( $label, $url, $current ) {
	$host     = wp_parse_url( home_url(), PHP_URL_HOST );
	$external = wp_parse_url( $url, PHP_URL_HOST ) && wp_parse_url( $url, PHP_URL_HOST ) !== $host;

	printf(
		'<a class="menu-link" href="%s"%s%s>%s%s</a>',
		esc_url( $url ),
		$current ? ' aria-current="page"' : '',
		$external ? ' target="_blank" rel="noopener noreferrer"' : '',
		esc_html( $label ),
		$external ? ' ' . lyk7_get_icon( 'external', 14, 'menu-link__ext' ) : '' // phpcs:ignore WordPress.Security.EscapeOutput
	);
}

/**
 * Is this URL the page being viewed (or its section)?
 *
 * @param string $url URL.
 * @return bool
 */
function lyk7_is_current( $url ) {
	static $here = null;
	if ( null === $here ) {
		$here = untrailingslashit( strtok( home_url( add_query_arg( array() ) ), '#' ) );
	}
	$url = untrailingslashit( strtok( (string) $url, '#' ) );
	if ( $url === untrailingslashit( home_url() ) ) {
		return $here === $url;
	}
	return $url && ( $here === $url || 0 === strpos( $here, $url . '/' ) );
}

/**
 * Built-in navigation. Children only for the primary menu.
 *
 * @param string $location Location.
 * @return array[] [ label, url, children? ]
 */
function lyk7_builtin_nav( $location ) {
	if ( 'primary' !== $location ) {
		return lyk7_default_links( $location );
	}

	$school   = get_page_by_path( 'to-scholeio-mas' );
	$children = array();
	if ( $school ) {
		foreach ( get_pages( array( 'parent' => $school->ID, 'sort_column' => 'menu_order,post_title' ) ) as $child ) {
			$children[] = array( get_the_title( $child ), get_permalink( $child ) );
		}
	}
	$children[] = array( 'Συλλογή φωτογραφιών', get_post_type_archive_link( 'gallery_item' ) );

	$items = lyk7_default_links( 'primary' );
	$items[0][2] = $children;

	return $items;
}
