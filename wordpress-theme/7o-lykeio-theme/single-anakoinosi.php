<?php
/**
 * Single announcement.
 *
 * @package lyk7
 */

get_header();
lyk7_breadcrumbs();

while ( have_posts() ) :
	the_post();
	$lyk7_urgent   = (bool) get_post_meta( get_the_ID(), '_lyk7_urgent', true );
	$lyk7_deadline = get_post_meta( get_the_ID(), '_lyk7_deadline', true );
	$lyk7_term     = lyk7_first_term( get_the_ID(), 'kathgoria_anakoinosis' );
	$lyk7_files    = lyk7_attachment_ids( get_the_ID() );
	?>
	<article class="single single--announcement<?php echo $lyk7_urgent ? ' is-urgent' : ''; ?>">
		<header class="single__head">
			<div class="wrap wrap--text">
				<p class="single__meta">
					<time datetime="<?php echo esc_attr( get_the_date( 'c' ) ); ?>"><?php echo esc_html( lyk7_date( get_post_timestamp() ) ); ?></time>
					<?php if ( $lyk7_urgent ) : ?>
						<span class="badge badge--urgent">Επείγον</span>
					<?php endif; ?>
					<?php if ( $lyk7_term ) : ?>
						<a class="badge badge--<?php echo esc_attr( lyk7_term_tone( $lyk7_term ) ); ?>" href="<?php echo esc_url( get_term_link( $lyk7_term ) ); ?>"><?php echo esc_html( $lyk7_term->name ); ?></a>
					<?php endif; ?>
				</p>
				<h1 class="single__title"><?php the_title(); ?></h1>
				<?php if ( $lyk7_deadline ) : ?>
					<p class="single__deadline">
						<?php lyk7_icon( 'calendar', 18 ); ?>
						<span>Προθεσμία: <time datetime="<?php echo esc_attr( $lyk7_deadline ); ?>"><?php echo esc_html( lyk7_date( $lyk7_deadline ) ); ?></time></span>
					</p>
				<?php endif; ?>
			</div>
		</header>

		<?php if ( has_post_thumbnail() ) : ?>
			<figure class="single__hero wrap"><?php the_post_thumbnail( 'lyk7-wide' ); ?></figure>
		<?php endif; ?>

		<div class="wrap wrap--text">
			<div class="prose"><?php the_content(); ?></div>

			<?php if ( $lyk7_files ) : ?>
				<section class="attachments" aria-labelledby="attachments-title">
					<h2 class="attachments__title" id="attachments-title"><?php lyk7_icon( 'clip', 20 ); ?> Συνημμένα αρχεία</h2>
					<ul class="doc-list">
						<?php foreach ( $lyk7_files as $lyk7_id ) : ?>
							<?php get_template_part( 'template-parts/doc-row', null, array( 'attachment' => $lyk7_id ) ); ?>
						<?php endforeach; ?>
					</ul>
				</section>
			<?php endif; ?>

			<?php
			$lyk7_prev = get_previous_post();
			$lyk7_next = get_next_post();
			if ( $lyk7_prev || $lyk7_next ) :
				?>
				<nav class="post-nav" aria-label="Πλοήγηση ανακοινώσεων">
					<?php if ( $lyk7_prev ) : ?>
						<a class="post-nav__link post-nav__link--prev" href="<?php echo esc_url( get_permalink( $lyk7_prev ) ); ?>">
							<span class="post-nav__label">Προηγούμενη</span>
							<span class="post-nav__title"><?php echo esc_html( get_the_title( $lyk7_prev ) ); ?></span>
						</a>
					<?php endif; ?>
					<?php if ( $lyk7_next ) : ?>
						<a class="post-nav__link post-nav__link--next" href="<?php echo esc_url( get_permalink( $lyk7_next ) ); ?>">
							<span class="post-nav__label">Επόμενη</span>
							<span class="post-nav__title"><?php echo esc_html( get_the_title( $lyk7_next ) ); ?></span>
						</a>
					<?php endif; ?>
				</nav>
			<?php endif; ?>
		</div>
	</article>

	<?php
	if ( $lyk7_term ) :
		$lyk7_related = new WP_Query(
			array(
				'post_type'      => 'anakoinosi',
				'posts_per_page' => 3,
				'post__not_in'   => array( get_the_ID() ),
				'no_found_rows'  => true,
				'tax_query'      => array( array( 'taxonomy' => 'kathgoria_anakoinosis', 'terms' => $lyk7_term->term_id ) ),
			)
		);
		if ( $lyk7_related->have_posts() ) :
			?>
			<section class="section section--related" aria-labelledby="related-title">
				<div class="wrap">
					<h2 class="section__title section__title--sm" id="related-title">Σχετικές ανακοινώσεις</h2>
					<div class="ann-list">
						<?php
						while ( $lyk7_related->have_posts() ) :
							$lyk7_related->the_post();
							get_template_part( 'template-parts/card-announcement' );
						endwhile;
						wp_reset_postdata();
						?>
					</div>
				</div>
			</section>
			<?php
		endif;
	endif;
endwhile;

get_footer();
