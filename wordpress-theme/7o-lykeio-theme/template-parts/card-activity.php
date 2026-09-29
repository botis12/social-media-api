<?php
/**
 * Activity card. Args: large (bool).
 *
 * @package lyk7
 */

$lyk7_large = ! empty( $args['large'] );
$lyk7_term  = lyk7_first_term( get_the_ID(), 'eidos_drastiriotitas' );
$lyk7_place = get_post_meta( get_the_ID(), '_lyk7_place', true );
$lyk7_date  = lyk7_activity_date( get_the_ID() );
?>
<article class="activity activity--<?php echo $lyk7_large ? 'large' : 'standard'; ?>" data-reveal data-tilt>
	<a class="activity__link" href="<?php the_permalink(); ?>">

		<div class="activity__media">
			<?php if ( has_post_thumbnail() ) : ?>
				<?php the_post_thumbnail( $lyk7_large ? 'lyk7-wide' : 'lyk7-card', array( 'loading' => 'lazy', 'alt' => get_the_title() ) ); ?>
			<?php else : ?>
				<span class="activity__placeholder" aria-hidden="true"><?php lyk7_icon( 'users', 40 ); ?></span>
			<?php endif; ?>
		</div>

		<div class="activity__body">
			<p class="activity__meta">
				<time datetime="<?php echo esc_attr( $lyk7_date ); ?>"><?php echo esc_html( lyk7_date( $lyk7_date ) ); ?></time>
				<?php if ( $lyk7_term ) : ?>
					<span class="activity__cat"><?php echo esc_html( $lyk7_term->name ); ?></span>
				<?php endif; ?>
			</p>

			<h3 class="activity__title"><?php the_title(); ?></h3>

			<p class="activity__excerpt"><?php echo esc_html( wp_trim_words( get_the_excerpt(), $lyk7_large ? 40 : 18, '…' ) ); ?></p>

			<?php if ( $lyk7_place ) : ?>
				<p class="activity__place"><?php lyk7_icon( 'pin', 15 ); ?> <span><?php echo esc_html( $lyk7_place ); ?></span></p>
			<?php endif; ?>
		</div>

	</a>
</article>
