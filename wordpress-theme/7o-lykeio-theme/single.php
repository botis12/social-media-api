<?php
/**
 * Any other single post.
 *
 * @package lyk7
 */

get_header();
lyk7_breadcrumbs();

while ( have_posts() ) :
	the_post();
	?>
	<article <?php post_class( 'single' ); ?>>
		<header class="single__head">
			<div class="wrap wrap--text">
				<p class="single__meta"><time datetime="<?php echo esc_attr( get_the_date( 'c' ) ); ?>"><?php echo esc_html( lyk7_date( get_post_timestamp() ) ); ?></time></p>
				<h1 class="single__title"><?php the_title(); ?></h1>
			</div>
		</header>
		<?php if ( has_post_thumbnail() ) : ?>
			<figure class="single__hero wrap"><?php the_post_thumbnail( 'lyk7-wide' ); ?></figure>
		<?php endif; ?>
		<div class="wrap wrap--text">
			<div class="prose"><?php the_content(); ?></div>
			<?php
			if ( comments_open() || get_comments_number() ) {
				comments_template();
			}
			?>
		</div>
	</article>
	<?php
endwhile;

get_footer();
