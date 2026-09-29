<?php
/**
 * Fallback listing (blog posts, dates, authors, tags …).
 *
 * @package lyk7
 */

get_header();
lyk7_breadcrumbs();
lyk7_page_head( is_home() ? single_post_title( '', false ) : wp_strip_all_tags( get_the_archive_title() ) );
?>
<div class="wrap section">
	<?php if ( have_posts() ) : ?>
		<div class="ann-list">
			<?php
			while ( have_posts() ) :
				the_post();
				?>
				<article class="ann ann--row" data-reveal>
					<div class="ann__body">
						<p class="ann__meta"><time class="ann__date" datetime="<?php echo esc_attr( get_the_date( 'c' ) ); ?>"><?php echo esc_html( lyk7_date( get_post_timestamp(), true ) ); ?></time></p>
						<h2 class="ann__title"><a href="<?php the_permalink(); ?>"><?php the_title(); ?></a></h2>
						<p class="ann__excerpt"><?php echo esc_html( get_the_excerpt() ); ?></p>
					</div>
				</article>
				<?php
			endwhile;
			?>
		</div>
		<?php lyk7_pagination(); ?>
	<?php else : ?>
		<?php lyk7_empty( 'Δεν βρέθηκε περιεχόμενο.' ); ?>
	<?php endif; ?>
</div>
<?php
get_footer();
