<?php
/**
 * Single activity.
 *
 * @package lyk7
 */

get_header();
lyk7_breadcrumbs();

while ( have_posts() ) :
	the_post();
	$lyk7_date  = lyk7_activity_date( get_the_ID() );
	$lyk7_term  = lyk7_first_term( get_the_ID(), 'eidos_drastiriotitas' );
	$lyk7_place = get_post_meta( get_the_ID(), '_lyk7_place', true );
	?>
	<article class="single single--activity">
		<header class="single__head">
			<div class="wrap wrap--text">
				<p class="single__meta">
					<time datetime="<?php echo esc_attr( $lyk7_date ); ?>"><?php echo esc_html( lyk7_date( $lyk7_date ) ); ?></time>
					<?php if ( $lyk7_term ) : ?>
						<a class="badge badge--life" href="<?php echo esc_url( get_term_link( $lyk7_term ) ); ?>"><?php echo esc_html( $lyk7_term->name ); ?></a>
					<?php endif; ?>
				</p>
				<h1 class="single__title"><?php the_title(); ?></h1>
				<?php if ( $lyk7_place ) : ?>
					<p class="single__place"><?php lyk7_icon( 'pin', 18 ); ?> <span><?php echo esc_html( $lyk7_place ); ?></span></p>
				<?php endif; ?>
			</div>
		</header>

		<?php if ( has_post_thumbnail() ) : ?>
			<figure class="single__hero wrap"><?php the_post_thumbnail( 'lyk7-wide', array( 'alt' => get_the_title() ) ); ?></figure>
		<?php endif; ?>

		<div class="wrap wrap--text">
			<div class="prose"><?php the_content(); ?></div>
		</div>
	</article>
	<?php
endwhile;

get_footer();
