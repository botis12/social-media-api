<?php
/**
 * Gallery tile. Args: caption (bool) — show caption under the photo.
 *
 * @package lyk7
 */

if ( ! has_post_thumbnail() ) {
	return;
}
$lyk7_caption = get_the_title();
?>
<li class="mosaic__item" data-reveal>
	<a class="mosaic__link" href="<?php echo esc_url( get_the_post_thumbnail_url( null, 'full' ) ); ?>" data-caption="<?php echo esc_attr( $lyk7_caption ); ?>">
		<?php the_post_thumbnail( 'lyk7-card', array( 'loading' => 'lazy', 'alt' => $lyk7_caption ) ); ?>
	</a>
	<?php if ( ! empty( $args['caption'] ) && $lyk7_caption ) : ?>
		<p class="mosaic__caption"><?php echo esc_html( $lyk7_caption ); ?></p>
	<?php endif; ?>
</li>
