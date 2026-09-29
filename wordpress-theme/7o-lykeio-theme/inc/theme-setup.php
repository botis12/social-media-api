<?php
/**
 * Theme supports, menus, image sizes, assets.
 *
 * @package lyk7
 */

defined( 'ABSPATH' ) || exit;

/**
 * Register theme features.
 */
function lyk7_setup() {
	load_theme_textdomain( 'lyk7', LYK7_DIR . '/languages' );

	add_theme_support( 'title-tag' );
	add_theme_support( 'automatic-feed-links' );
	add_theme_support( 'post-thumbnails' );
	add_theme_support( 'responsive-embeds' );
	add_theme_support( 'wp-block-styles' );
	add_theme_support( 'align-wide' );
	add_theme_support( 'html5', array( 'search-form', 'comment-form', 'comment-list', 'gallery', 'caption', 'style', 'script', 'navigation-widgets' ) );
	add_theme_support(
		'custom-logo',
		array(
			'height'      => 223,
			'width'       => 383,
			'flex-height' => true,
			'flex-width'  => true,
		)
	);

	add_image_size( 'lyk7-card', 800, 534, false );
	add_image_size( 'lyk7-wide', 1600, 1000, false );

	register_nav_menus(
		array(
			'primary'         => 'Κύριο μενού',
			'footer-quick'    => 'Υποσέλιδο — Γρήγοροι σύνδεσμοι',
			'footer-external' => 'Υποσέλιδο — Χρήσιμοι σύνδεσμοι',
			'legal'           => 'Υποσέλιδο — Θεσμικά',
		)
	);
}
add_action( 'after_setup_theme', 'lyk7_setup' );

/**
 * Content width for embeds.
 */
function lyk7_content_width() {
	$GLOBALS['content_width'] = 760;
}
add_action( 'after_setup_theme', 'lyk7_content_width', 0 );

/**
 * Front-end styles and scripts.
 */
function lyk7_assets() {
	wp_enqueue_style(
		'lyk7-fonts',
		'https://fonts.googleapis.com/css2?family=Alegreya:wght@500;700&family=Commissioner:wght@400;500;600&display=swap&subset=greek,latin',
		array(),
		null
	);
	wp_enqueue_style( 'lyk7-style', get_stylesheet_uri(), array(), LYK7_VERSION );
	wp_enqueue_style( 'lyk7-print', LYK7_URI . '/assets/css/print.css', array(), LYK7_VERSION, 'print' );

	wp_enqueue_script( 'lyk7-nav', LYK7_URI . '/assets/js/nav.js', array(), LYK7_VERSION, array( 'strategy' => 'defer', 'in_footer' => true ) );
	wp_enqueue_script( 'lyk7-motion', LYK7_URI . '/assets/js/motion.js', array(), LYK7_VERSION, array( 'strategy' => 'defer', 'in_footer' => true ) );

	wp_enqueue_script( 'lyk7-gallery', LYK7_URI . '/assets/js/gallery.js', array(), LYK7_VERSION, array( 'strategy' => 'defer', 'in_footer' => true ) );
	wp_localize_script(
		'lyk7-gallery',
		'lyk7Gallery',
		array(
			'close' => 'Κλείσιμο',
			'prev'  => 'Προηγούμενη φωτογραφία',
			'next'  => 'Επόμενη φωτογραφία',
			'of'    => 'από',
		)
	);

	if ( is_post_type_archive( 'eggrafo' ) || is_tax( array( 'eidos_eggrafou', 'sxoliko_etos' ) ) ) {
		wp_enqueue_script( 'lyk7-docs', LYK7_URI . '/assets/js/docs-filter.js', array(), LYK7_VERSION, array( 'strategy' => 'defer', 'in_footer' => true ) );
		wp_localize_script(
			'lyk7-docs',
			'lyk7Docs',
			array(
				'none' => 'Δεν βρέθηκαν έγγραφα με αυτά τα κριτήρια.',
				'one'  => '1 έγγραφο',
				'many' => '%s έγγραφα',
			)
		);
	}

	if ( is_singular() && comments_open() && get_option( 'thread_comments' ) ) {
		wp_enqueue_script( 'comment-reply' );
	}
}
add_action( 'wp_enqueue_scripts', 'lyk7_assets' );

/**
 * Preconnect to the font host.
 *
 * @param array  $urls          URLs.
 * @param string $relation_type Relation.
 * @return array
 */
function lyk7_resource_hints( $urls, $relation_type ) {
	if ( 'preconnect' === $relation_type ) {
		$urls[] = 'https://fonts.googleapis.com';
		$urls[] = array(
			'href' => 'https://fonts.gstatic.com',
			'crossorigin',
		);
	}
	return $urls;
}
add_filter( 'wp_resource_hints', 'lyk7_resource_hints', 10, 2 );

/**
 * Body classes used by the stylesheet.
 *
 * @param string[] $classes Classes.
 * @return string[]
 */
function lyk7_body_class( $classes ) {
	if ( is_archive() || is_search() || is_home() ) {
		$classes[] = 'is-listing';
	}
	if ( is_front_page() ) {
		$classes[] = 'is-home';
	}
	return $classes;
}
add_filter( 'body_class', 'lyk7_body_class' );

/**
 * Description and Open Graph tags — enough for a clean share preview.
 * Skipped when an SEO plugin is active.
 */
function lyk7_meta_tags() {
	if ( defined( 'WPSEO_VERSION' ) || defined( 'RANK_MATH_VERSION' ) || defined( 'AIOSEO_VERSION' ) ) {
		return;
	}

	$title = wp_get_document_title();
	$desc  = get_bloginfo( 'description' );
	$image = lyk7_image_url( 'hero_image', 'assets/images/school-05.jpg' );
	$url   = home_url( add_query_arg( array() ) );

	if ( is_singular() ) {
		$post = get_queried_object();
		if ( $post && has_excerpt( $post ) ) {
			$desc = get_the_excerpt( $post );
		} elseif ( $post ) {
			$desc = wp_trim_words( wp_strip_all_tags( $post->post_content ), 30, '…' );
		}
		if ( has_post_thumbnail( $post ) ) {
			$image = get_the_post_thumbnail_url( $post, 'lyk7-wide' );
		}
		$url = get_permalink( $post );
	}

	$desc = trim( wp_strip_all_tags( (string) $desc ) );

	if ( $desc ) {
		printf( '<meta name="description" content="%s">' . "\n", esc_attr( $desc ) );
	}
	printf( '<meta property="og:type" content="%s">' . "\n", is_singular() ? 'article' : 'website' );
	echo '<meta property="og:locale" content="el_GR">' . "\n";
	printf( '<meta property="og:site_name" content="%s">' . "\n", esc_attr( get_bloginfo( 'name' ) ) );
	printf( '<meta property="og:title" content="%s">' . "\n", esc_attr( $title ) );
	if ( $desc ) {
		printf( '<meta property="og:description" content="%s">' . "\n", esc_attr( $desc ) );
	}
	printf( '<meta property="og:url" content="%s">' . "\n", esc_url( $url ) );
	if ( $image ) {
		printf( '<meta property="og:image" content="%s">' . "\n", esc_url( $image ) );
	}
	echo '<meta name="twitter:card" content="summary_large_image">' . "\n";
}
add_action( 'wp_head', 'lyk7_meta_tags', 5 );

/**
 * Shorter, cleaner excerpts.
 *
 * @return int
 */
function lyk7_excerpt_length() {
	return 22;
}
add_filter( 'excerpt_length', 'lyk7_excerpt_length' );

/**
 * Ellipsis instead of [...].
 *
 * @return string
 */
function lyk7_excerpt_more() {
	return '…';
}
add_filter( 'excerpt_more', 'lyk7_excerpt_more' );

/**
 * Block editor: load the theme fonts and base styles in the editor too.
 */
function lyk7_editor_assets() {
	wp_enqueue_style(
		'lyk7-editor-fonts',
		'https://fonts.googleapis.com/css2?family=Alegreya:wght@500;700&family=Commissioner:wght@400;500;600&display=swap&subset=greek,latin',
		array(),
		null
	);
}
add_action( 'enqueue_block_editor_assets', 'lyk7_editor_assets' );
