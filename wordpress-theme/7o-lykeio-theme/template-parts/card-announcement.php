<?php
/**
 * Announcement card. Args: variant (row|featured), heading (h2|h3).
 *
 * @package lyk7
 */

$lyk7_variant = $args['variant'] ?? 'row';
$lyk7_heading = $args['heading'] ?? 'h3';
$lyk7_urgent  = (bool) get_post_meta( get_the_ID(), '_lyk7_urgent', true );
$lyk7_term    = lyk7_first_term( get_the_ID(), 'kathgoria_anakoinosis' );
$lyk7_files   = lyk7_attachment_ids( get_the_ID() );
?>
<article class="ann ann--<?php echo esc_attr( $lyk7_variant ); ?><?php echo $lyk7_urgent ? ' is-urgent' : ''; ?>" data-reveal>

	<?php if ( 'featured' === $lyk7_variant && has_post_thumbnail() ) : ?>
		<div class="ann__media"><?php the_post_thumbnail( 'lyk7-card', array( 'loading' => 'lazy' ) ); ?></div>
	<?php endif; ?>

	<div class="ann__body">
		<p class="ann__meta">
			<time class="ann__date" datetime="<?php echo esc_attr( get_the_date( 'c' ) ); ?>"><?php echo esc_html( lyk7_date( get_post_timestamp(), true ) ); ?></time>
			<?php if ( $lyk7_urgent ) : ?>
				<span class="badge badge--urgent">Επείγον</span>
			<?php endif; ?>
			<?php if ( $lyk7_term ) : ?>
				<a class="badge badge--<?php echo esc_attr( lyk7_term_tone( $lyk7_term ) ); ?>" href="<?php echo esc_url( get_term_link( $lyk7_term ) ); ?>"><?php echo esc_html( $lyk7_term->name ); ?></a>
			<?php endif; ?>
		</p>

		<<?php echo esc_html( $lyk7_heading ); ?> class="ann__title"><a href="<?php the_permalink(); ?>"><?php the_title(); ?></a></<?php echo esc_html( $lyk7_heading ); ?>>

		<p class="ann__excerpt"><?php echo esc_html( wp_trim_words( get_the_excerpt(), 'featured' === $lyk7_variant ? 30 : 20, '…' ) ); ?></p>

		<?php if ( $lyk7_files ) : ?>
			<p class="ann__files"><?php lyk7_icon( 'clip', 15 ); ?> <?php echo esc_html( 1 === count( $lyk7_files ) ? '1 συνημμένο' : count( $lyk7_files ) . ' συνημμένα' ); ?></p>
		<?php endif; ?>
	</div>
</article>
