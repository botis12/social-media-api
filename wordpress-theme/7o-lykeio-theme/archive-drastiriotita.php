<?php
/**
 * Activities archive (also used for activity types).
 *
 * @package lyk7
 */

get_header();
lyk7_breadcrumbs();

if ( is_tax() ) {
	lyk7_page_head( single_term_title( '', false ), 'Ζωή του σχολείου', wp_strip_all_tags( term_description() ), 'page-head--life' );
} else {
	lyk7_page_head( 'Η ζωή του σχολείου', 'Δράσεις και εκδηλώσεις', 'Εκδηλώσεις, επιμορφώσεις, εκδρομές, επισκέψεις και προγράμματα.', 'page-head--life' );
}
lyk7_chip_bar( 'eidos_drastiriotitas', 'drastiriotita', 'Φίλτρο ειδών δράσης' );
?>
<div class="wrap section">
	<?php if ( have_posts() ) : ?>
		<div class="life-grid life-grid--archive" data-tilt-scene>
			<?php
			while ( have_posts() ) :
				the_post();
				get_template_part( 'template-parts/card-activity' );
			endwhile;
			?>
		</div>
		<?php lyk7_pagination(); ?>
	<?php else : ?>
		<?php lyk7_empty( 'Δεν υπάρχουν δραστηριότητες ακόμη.' ); ?>
	<?php endif; ?>
</div>
<?php
get_footer();
