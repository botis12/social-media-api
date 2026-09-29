<?php
/**
 * 7ο ΓΕΛ Ιλίου — theme bootstrap.
 *
 * Everything the site needs lives in the theme: content types, taxonomies,
 * editor fields, Customizer options and a one-click setup that creates the
 * pages, menus and demo content on activation.
 *
 * @package lyk7
 */

defined( 'ABSPATH' ) || exit;

define( 'LYK7_VERSION', '1.2.0' );
define( 'LYK7_DIR', get_template_directory() );
define( 'LYK7_URI', get_template_directory_uri() );

require LYK7_DIR . '/inc/helpers.php';
require LYK7_DIR . '/inc/theme-setup.php';
require LYK7_DIR . '/inc/post-types.php';
require LYK7_DIR . '/inc/meta-boxes.php';
require LYK7_DIR . '/inc/customizer.php';
require LYK7_DIR . '/inc/template-tags.php';
require LYK7_DIR . '/inc/class-lyk7-nav-walker.php';
require LYK7_DIR . '/inc/queries.php';
require LYK7_DIR . '/inc/installer.php';
require LYK7_DIR . '/inc/admin.php';
