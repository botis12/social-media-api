<?php
/**
 * Document row. Works for an eggrafo post, or an attachment via $args['attachment'].
 *
 * @package lyk7
 */

if ( ! empty( $args['attachment'] ) ) {
	$lyk7_att   = (int) $args['attachment'];
	$lyk7_url   = wp_get_attachment_url( $lyk7_att );
	$lyk7_title = get_the_title( $lyk7_att );
	$lyk7_kind  = null;
	$lyk7_year  = null;
} else {
	$lyk7_att   = (int) get_post_meta( get_the_ID(), '_lyk7_file_id', true );
	$lyk7_url   = lyk7_doc_url( get_the_ID() );
	$lyk7_title = get_the_title();
	$lyk7_kind  = lyk7_first_term( get_the_ID(), 'eidos_eggrafou' );
	$lyk7_year  = lyk7_first_term( get_the_ID(), 'sxoliko_etos' );
}

$lyk7_info  = lyk7_file_info( $lyk7_att, $lyk7_url );
$lyk7_ext   = 'link' === $lyk7_info['type'];
$lyk7_label = $lyk7_title . ' — ' . ( $lyk7_ext ? 'εξωτερικός σύνδεσμος' : $lyk7_info['label'] . ( $lyk7_info['size'] ? ' ' . $lyk7_info['size'] : '' ) );
?>
<li class="doc"
	data-kind="<?php echo esc_attr( $lyk7_kind ? $lyk7_kind->slug : '' ); ?>"
	data-year="<?php echo esc_attr( $lyk7_year ? $lyk7_year->slug : '' ); ?>"
	data-type="<?php echo esc_attr( $lyk7_info['type'] ); ?>"
	data-title="<?php echo esc_attr( mb_strtolower( $lyk7_title ) ); ?>"
	data-reveal>

	<a class="doc__link" href="<?php echo esc_url( $lyk7_url ? $lyk7_url : '#' ); ?>" aria-label="<?php echo esc_attr( $lyk7_label ); ?>"<?php echo $lyk7_ext ? ' target="_blank" rel="noopener noreferrer"' : ''; ?>>

		<span class="doc__type doc__type--<?php echo esc_attr( $lyk7_info['type'] ); ?>" aria-hidden="true"><?php echo esc_html( $lyk7_info['label'] ); ?></span>

		<span class="doc__main">
			<span class="doc__title"><?php echo esc_html( $lyk7_title ); ?></span>
			<span class="doc__meta">
				<?php if ( $lyk7_kind ) : ?>
					<span class="doc__kind"><?php echo esc_html( $lyk7_kind->name ); ?></span>
				<?php endif; ?>
				<?php if ( $lyk7_year ) : ?>
					<span class="doc__year"><?php echo esc_html( $lyk7_year->name ); ?></span>
				<?php endif; ?>
				<?php if ( $lyk7_info['size'] ) : ?>
					<span class="doc__size"><?php echo esc_html( $lyk7_info['size'] ); ?></span>
				<?php endif; ?>
			</span>
		</span>

		<span class="doc__action" aria-hidden="true"><?php lyk7_icon( $lyk7_ext ? 'external' : 'download', 19 ); ?></span>
	</a>
</li>
