<?php
/**
 * Small, dependency-free helpers: icons, Greek dates, options.
 *
 * @package lyk7
 */

defined( 'ABSPATH' ) || exit;

/**
 * Inline SVG icon. Stroke icons drawn on a 24px grid.
 *
 * @param string $name  Icon key.
 * @param int    $size  Rendered size in px.
 * @param string $class Extra classes.
 * @return string
 */
function lyk7_get_icon( $name, $size = 20, $class = '' ) {
	$paths = array(
		'phone'    => '<path d="M5 4h4l2 5-2.5 1.5a12 12 0 0 0 5 5L15 13l5 2v4a1 1 0 0 1-1 1A16 16 0 0 1 4 5a1 1 0 0 1 1-1z"/>',
		'mail'     => '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>',
		'search'   => '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.6-3.6"/>',
		'arrow'    => '<path d="M5 12h13"/><path d="m13 6 6 6-6 6"/>',
		'calendar' => '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
		'clock'    => '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
		'pen'      => '<path d="M4 20h4L19 9a2.1 2.1 0 0 0-3-3L5 17z"/><path d="M14.5 6.5l3 3"/>',
		'file'     => '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/>',
		'users'    => '<circle cx="9" cy="8" r="3.2"/><path d="M3 20a6 6 0 0 1 12 0"/><path d="M16 5.5a3.2 3.2 0 0 1 0 6"/><path d="M17.5 14.5A6 6 0 0 1 21 20"/>',
		'book'     => '<path d="M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2z"/><path d="M4 17a2 2 0 0 1 2-2h13"/>',
		'flask'    => '<path d="M10 3v6.5L4.6 18A2 2 0 0 0 6.3 21h11.4a2 2 0 0 0 1.7-3L14 9.5V3"/><path d="M9 3h6"/>',
		'pin'      => '<path d="M12 21s7-6.2 7-11a7 7 0 1 0-14 0c0 4.8 7 11 7 11z"/><circle cx="12" cy="10" r="2.6"/>',
		'download' => '<path d="M12 4v11"/><path d="M8 11l4 4 4-4"/><path d="M4 19h16"/>',
		'external' => '<path d="M14 4h6v6"/><path d="M20 4 10 14"/><path d="M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/>',
		'clip'     => '<path d="m20 11-8.5 8.5a5 5 0 0 1-7-7L13 4a3.3 3.3 0 0 1 4.7 4.7L9.2 17.2a1.7 1.7 0 0 1-2.4-2.4L14.5 7"/>',
		'image'    => '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="2"/><path d="m21 16-5-5-9 9"/>',
		'link'     => '<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1"/><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/>',
	);

	if ( ! isset( $paths[ $name ] ) ) {
		$name = 'arrow';
	}

	return sprintf(
		'<svg class="icon %1$s" width="%2$d" height="%2$d" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">%3$s</svg>',
		esc_attr( $class ),
		(int) $size,
		$paths[ $name ]
	);
}

/**
 * Echo an icon.
 *
 * @param string $name  Icon key.
 * @param int    $size  Size.
 * @param string $class Extra classes.
 */
function lyk7_icon( $name, $size = 20, $class = '' ) {
	echo lyk7_get_icon( $name, $size, $class ); // phpcs:ignore WordPress.Security.EscapeOutput -- static markup.
}

/**
 * Icons offered for quick-access tiles.
 *
 * @return string[]
 */
function lyk7_icon_names() {
	return array( 'clock', 'pen', 'file', 'users', 'book', 'flask', 'mail', 'phone', 'calendar', 'pin', 'image', 'link' );
}

/* -------------------------------------------------------------------------
 * Greek dates
 *
 * Built in, so the site reads correctly in Greek even when the WordPress
 * admin language is English.
 * ---------------------------------------------------------------------- */

/**
 * Month names: genitive (full dates) and short.
 *
 * @param bool $short Short form.
 * @return string[]
 */
function lyk7_months( $short = false ) {
	if ( $short ) {
		return array( 1 => 'Ιαν', 'Φεβ', 'Μαρ', 'Απρ', 'Μάι', 'Ιούν', 'Ιούλ', 'Αύγ', 'Σεπ', 'Οκτ', 'Νοέ', 'Δεκ' );
	}

	return array( 1 => 'Ιανουαρίου', 'Φεβρουαρίου', 'Μαρτίου', 'Απριλίου', 'Μαΐου', 'Ιουνίου', 'Ιουλίου', 'Αυγούστου', 'Σεπτεμβρίου', 'Οκτωβρίου', 'Νοεμβρίου', 'Δεκεμβρίου' );
}

/**
 * Turn a timestamp or Y-m-d string into a DateTimeImmutable in the site zone.
 *
 * @param int|string $value Timestamp or date string.
 * @return DateTimeImmutable|null
 */
function lyk7_to_datetime( $value ) {
	if ( '' === $value || null === $value || false === $value ) {
		return null;
	}

	try {
		if ( is_numeric( $value ) ) {
			return ( new DateTimeImmutable( '@' . (int) $value ) )->setTimezone( wp_timezone() );
		}
		return new DateTimeImmutable( (string) $value, wp_timezone() );
	} catch ( Exception $e ) {
		return null;
	}
}

/**
 * "22 Σεπτεμβρίου 2026" or "22 Σεπ 2026".
 *
 * @param int|string $value Timestamp or date string.
 * @param bool       $short Use short month.
 * @return string
 */
function lyk7_date( $value, $short = false ) {
	$dt = lyk7_to_datetime( $value );
	if ( ! $dt ) {
		return '';
	}

	$months = lyk7_months( $short );

	return $dt->format( 'j' ) . ' ' . $months[ (int) $dt->format( 'n' ) ] . ' ' . $dt->format( 'Y' );
}

/**
 * "20/5" — day and month, for the compact "today" strip.
 *
 * @param string $value Date string.
 * @return string
 */
function lyk7_date_compact( $value ) {
	$dt = lyk7_to_datetime( $value );
	return $dt ? $dt->format( 'j/n' ) : '';
}

/* -------------------------------------------------------------------------
 * Options
 * ---------------------------------------------------------------------- */

/**
 * Read a Customizer option, falling back to the theme default.
 *
 * @param string $key Option key (without prefix).
 * @return mixed
 */
function lyk7_opt( $key ) {
	$defaults = lyk7_defaults();
	$default  = isset( $defaults[ $key ] ) ? $defaults[ $key ] : '';
	$value    = get_theme_mod( 'lyk7_' . $key, $default );

	return ( '' === $value || null === $value ) ? $default : $value;
}

/**
 * Split a "a | b | c" textarea into rows of trimmed cells.
 *
 * @param string $text  Raw textarea value.
 * @param int    $cells Number of cells to pad each row to.
 * @return array[]
 */
function lyk7_parse_lines( $text, $cells = 2 ) {
	$rows = array();

	foreach ( preg_split( '/\r\n|\r|\n/', (string) $text ) as $line ) {
		$line = trim( $line );
		if ( '' === $line ) {
			continue;
		}

		$parts = array_map( 'trim', explode( '|', $line ) );
		$rows[] = array_pad( $parts, $cells, '' );
	}

	return $rows;
}

/**
 * Resolve a URL typed into the Customizer. "/path" is relative to the site.
 *
 * @param string $url Raw URL.
 * @return string
 */
function lyk7_resolve_url( $url ) {
	$url = trim( (string) $url );

	if ( '' === $url ) {
		return home_url( '/' );
	}
	if ( '/' === $url[0] && ( ! isset( $url[1] ) || '/' !== $url[1] ) ) {
		return home_url( $url );
	}
	if ( '#' === $url[0] ) {
		return home_url( '/' . $url );
	}

	return $url;
}

/**
 * Phone numbers from the Customizer as [ label, [ numbers ] ].
 *
 * @return array[]
 */
function lyk7_phones() {
	$out = array();

	foreach ( lyk7_parse_lines( lyk7_opt( 'phones' ), 2 ) as $row ) {
		$numbers = array_filter( array_map( 'trim', explode( ',', $row[1] ) ) );
		if ( $numbers ) {
			$out[] = array( $row[0], array_values( $numbers ) );
		}
	}

	return $out;
}

/**
 * A tel: link for a displayed number.
 *
 * @param string $number Human-readable number.
 * @return string
 */
function lyk7_tel( $number ) {
	return 'tel:' . preg_replace( '/[^0-9+]/', '', $number );
}

/**
 * Timetable rows: [ label, start, end ].
 *
 * @return array[]
 */
function lyk7_timetable() {
	return lyk7_parse_lines( lyk7_opt( 'timetable' ), 3 );
}

/**
 * Image source for a Customizer image option (attachment ID or URL), or the
 * bundled default.
 *
 * @param string $key      Option key.
 * @param string $fallback Theme-relative path of the bundled image.
 * @return string
 */
function lyk7_image_url( $key, $fallback ) {
	$value = get_theme_mod( 'lyk7_' . $key );

	if ( is_numeric( $value ) && $value ) {
		$src = wp_get_attachment_image_url( (int) $value, 'full' );
		if ( $src ) {
			return $src;
		}
	} elseif ( is_string( $value ) && '' !== $value ) {
		return $value;
	}

	return LYK7_URI . '/' . ltrim( $fallback, '/' );
}
