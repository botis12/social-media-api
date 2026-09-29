<?php
/**
 * Template tags shared across templates.
 *
 * @package lyk7
 */

defined( 'ABSPATH' ) || exit;

/* ------------------------------------------------------------------ */
/* Data helpers                                                         */
/* ------------------------------------------------------------------ */

/**
 * First term of a taxonomy for a post.
 *
 * @param int    $post_id  Post ID.
 * @param string $taxonomy Taxonomy.
 * @return WP_Term|null
 */
function lyk7_first_term( $post_id, $taxonomy ) {
	$terms = get_the_terms( $post_id, $taxonomy );
	return ( $terms && ! is_wp_error( $terms ) ) ? $terms[0] : null;
}

/**
 * Activity date: event date, else publish date.
 *
 * @param int $post_id Post ID.
 * @return string Y-m-d
 */
function lyk7_activity_date( $post_id ) {
	$date = get_post_meta( $post_id, '_lyk7_event_date', true );
	return $date ? $date : get_the_date( 'Y-m-d', $post_id );
}

/**
 * Document download URL.
 *
 * @param int $post_id Post ID.
 * @return string
 */
function lyk7_doc_url( $post_id ) {
	$file_id = (int) get_post_meta( $post_id, '_lyk7_file_id', true );
	if ( $file_id ) {
		$url = wp_get_attachment_url( $file_id );
		if ( $url ) {
			return $url;
		}
	}
	return (string) get_post_meta( $post_id, '_lyk7_file_url', true );
}

/**
 * File type badge (pdf, doc, xls, ppt, link) and human size for an attachment.
 *
 * @param int    $attachment_id Attachment ID (0 for external link).
 * @param string $url           URL (for the extension when there is no attachment).
 * @return array{type:string,label:string,size:string}
 */
function lyk7_file_info( $attachment_id, $url = '' ) {
	$path = $attachment_id ? (string) get_attached_file( $attachment_id ) : '';
	$ext  = strtolower( pathinfo( $path ? $path : (string) wp_parse_url( $url, PHP_URL_PATH ), PATHINFO_EXTENSION ) );

	$map = array(
		'pdf'  => 'pdf',
		'doc'  => 'doc',
		'docx' => 'doc',
		'odt'  => 'doc',
		'xls'  => 'xls',
		'xlsx' => 'xls',
		'ods'  => 'xls',
		'ppt'  => 'ppt',
		'pptx' => 'ppt',
		'ppsx' => 'ppt',
	);

	$type = ( $attachment_id || isset( $map[ $ext ] ) ) && isset( $map[ $ext ] ) ? $map[ $ext ] : ( $attachment_id ? 'doc' : 'link' );
	$size = ( $path && file_exists( $path ) ) ? size_format( filesize( $path ) ) : '';

	return array(
		'type'  => $type,
		'label' => 'link' === $type ? '↗' : strtoupper( $ext ? $ext : $type ),
		'size'  => $size ? str_replace( 'KB', 'kB', $size ) : '',
	);
}

/**
 * Upcoming deadline announcement (nearest in the future).
 *
 * @return WP_Post|null
 */
function lyk7_next_deadline() {
	$q = new WP_Query(
		array(
			'post_type'      => 'anakoinosi',
			'posts_per_page' => 1,
			'no_found_rows'  => true,
			'meta_key'       => '_lyk7_deadline',
			'orderby'        => 'meta_value',
			'order'          => 'ASC',
			'meta_query'     => array(
				array(
					'key'     => '_lyk7_deadline',
					'value'   => wp_date( 'Y-m-d' ),
					'compare' => '>=',
					'type'    => 'DATE',
				),
			),
		)
	);
	return $q->posts ? $q->posts[0] : null;
}

/**
 * Current lesson hour, if school is in session right now.
 *
 * @return array|null [ label, start, end ]
 */
function lyk7_current_period() {
	$dow = (int) wp_date( 'N' );
	if ( $dow > 5 ) {
		return null;
	}
	$now = wp_date( 'H:i' );
	foreach ( lyk7_timetable() as $row ) {
		if ( $row[1] && $row[2] && $now >= $row[1] && $now < $row[2] ) {
			return $row;
		}
	}
	return null;
}

/* ------------------------------------------------------------------ */
/* Chrome                                                               */
/* ------------------------------------------------------------------ */

/**
 * Breadcrumbs.
 */
function lyk7_breadcrumbs() {
	if ( is_front_page() ) {
		return;
	}

	$items = array( array( home_url( '/' ), 'Αρχική' ) );

	if ( is_singular() ) {
		$post = get_queried_object();
		if ( 'page' === $post->post_type ) {
			foreach ( array_reverse( get_post_ancestors( $post ) ) as $ancestor ) {
				$items[] = array( get_permalink( $ancestor ), get_the_title( $ancestor ) );
			}
		} elseif ( 'post' !== $post->post_type ) {
			$pto     = get_post_type_object( $post->post_type );
			$items[] = array( get_post_type_archive_link( $post->post_type ), $pto->labels->name );
		}
		$items[] = array( '', get_the_title( $post ) );
	} elseif ( is_tax() ) {
		$term = get_queried_object();
		$tax  = get_taxonomy( $term->taxonomy );
		$pt   = $tax->object_type[0];
		$pto  = get_post_type_object( $pt );
		$items[] = array( get_post_type_archive_link( $pt ), 'drastiriotita' === $pt ? 'Ζωή του σχολείου' : $pto->labels->name );
		$items[] = array( '', $term->name );
	} elseif ( is_post_type_archive() ) {
		$items[] = array( '', lyk7_archive_crumb( get_query_var( 'post_type' ) ) );
	} elseif ( is_search() ) {
		$items[] = array( '', 'Αναζήτηση' );
	} elseif ( is_404() ) {
		$items[] = array( '', 'Η σελίδα δεν βρέθηκε' );
	} elseif ( is_archive() || is_home() ) {
		$items[] = array( '', wp_strip_all_tags( get_the_archive_title() ) );
	}

	echo '<nav class="breadcrumbs" aria-label="Διαδρομή πλοήγησης"><ol>';
	foreach ( $items as $item ) {
		if ( $item[0] ) {
			printf( '<li><a href="%s">%s</a></li>', esc_url( $item[0] ), esc_html( $item[1] ) );
		} else {
			printf( '<li><span aria-current="page">%s</span></li>', esc_html( $item[1] ) );
		}
	}
	echo '</ol></nav>';
}

/**
 * Breadcrumb label for a post type archive.
 *
 * @param string|array $post_type Post type.
 * @return string
 */
function lyk7_archive_crumb( $post_type ) {
	$post_type = is_array( $post_type ) ? reset( $post_type ) : $post_type;
	$labels    = array(
		'anakoinosi'    => 'Ανακοινώσεις',
		'drastiriotita' => 'Ζωή του σχολείου',
		'eggrafo'       => 'Έγγραφα',
		'gallery_item'  => 'Στιγμιότυπα',
	);
	return isset( $labels[ $post_type ] ) ? $labels[ $post_type ] : post_type_archive_title( '', false );
}

/**
 * Page heading block.
 *
 * @param string $title   Title.
 * @param string $eyebrow Small label above.
 * @param string $lede    Intro text.
 * @param string $mod     Modifier class.
 */
function lyk7_page_head( $title, $eyebrow = '', $lede = '', $mod = '' ) {
	?>
	<div class="page-head<?php echo $mod ? ' ' . esc_attr( $mod ) : ''; ?>">
		<div class="wrap">
			<?php if ( $eyebrow ) : ?>
				<p class="eyebrow"><?php echo esc_html( $eyebrow ); ?></p>
			<?php endif; ?>
			<h1 class="page-head__title"><?php echo esc_html( $title ); ?></h1>
			<?php if ( $lede ) : ?>
				<p class="page-head__lede"><?php echo esc_html( $lede ); ?></p>
			<?php endif; ?>
		</div>
	</div>
	<?php
}

/**
 * Filter chips for a taxonomy.
 *
 * @param string $taxonomy  Taxonomy.
 * @param string $post_type Post type for the "all" chip.
 * @param string $label     aria-label.
 * @param string $all       Text of the "all" chip.
 */
function lyk7_chip_bar( $taxonomy, $post_type, $label, $all = 'Όλες' ) {
	$terms = get_terms( array( 'taxonomy' => $taxonomy, 'hide_empty' => true ) );
	if ( ! $terms || is_wp_error( $terms ) ) {
		return;
	}
	$current = is_tax( $taxonomy ) ? get_queried_object_id() : 0;
	?>
	<nav class="chip-bar" aria-label="<?php echo esc_attr( $label ); ?>">
		<div class="wrap">
			<ul class="chip-bar__list">
				<li>
					<a class="chip<?php echo $current ? '' : ' is-active'; ?>" href="<?php echo esc_url( get_post_type_archive_link( $post_type ) ); ?>"<?php echo $current ? '' : ' aria-current="page"'; ?>><?php echo esc_html( $all ); ?></a>
				</li>
				<?php foreach ( $terms as $term ) : ?>
					<?php $tone = 'kathgoria_anakoinosis' === $taxonomy ? lyk7_term_tone( $term ) : 'life'; ?>
					<li>
						<a class="chip chip--<?php echo esc_attr( $tone ); ?><?php echo $current === $term->term_id ? ' is-active' : ''; ?>" href="<?php echo esc_url( get_term_link( $term ) ); ?>"<?php echo $current === $term->term_id ? ' aria-current="page"' : ''; ?>>
							<?php echo esc_html( $term->name ); ?>
							<span class="chip__count"><?php echo (int) $term->count; ?></span>
						</a>
					</li>
				<?php endforeach; ?>
			</ul>
		</div>
	</nav>
	<?php
}

/**
 * Numbered pagination.
 */
function lyk7_pagination() {
	$links = paginate_links(
		array(
			'type'      => 'array',
			'mid_size'  => 1,
			'prev_text' => lyk7_get_icon( 'arrow', 16, 'is-back' ) . '<span>Προηγούμενα</span>',
			'next_text' => '<span>Επόμενα</span>' . lyk7_get_icon( 'arrow', 16 ),
		)
	);
	if ( ! $links ) {
		return;
	}
	echo '<nav class="pagination" aria-label="Σελίδες"><ul>';
	foreach ( $links as $link ) {
		echo '<li>' . $link . '</li>'; // phpcs:ignore WordPress.Security.EscapeOutput -- core markup.
	}
	echo '</ul></nav>';
}

/**
 * Empty state.
 *
 * @param string $text Message.
 */
function lyk7_empty( $text ) {
	printf( '<div class="empty-state"><p class="empty-state__title">%s</p></div>', esc_html( $text ) );
}
