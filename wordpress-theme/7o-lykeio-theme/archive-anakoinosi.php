<?php
/**
 * Announcements archive (also used for announcement categories).
 *
 * @package lyk7
 */

get_header();
lyk7_breadcrumbs();

if ( is_tax() ) {
	lyk7_page_head( single_term_title( '', false ), 'Ανακοινώσεις', wp_strip_all_tags( term_description() ) );
} else {
	lyk7_page_head( 'Ανακοινώσεις', 'Ενημέρωση', 'Ενημερώσεις προς μαθητές, γονείς, κηδεμόνες και εκπαιδευτικούς.' );
}
lyk7_chip_bar( 'kathgoria_anakoinosis', 'anakoinosi', 'Φίλτρο κατηγοριών' );
?>
<div class="wrap section">
	<?php if ( have_posts() ) : ?>
		<div class="ann-list">
			<?php
			while ( have_posts() ) :
				the_post();
				get_template_part( 'template-parts/card-announcement', null, array( 'heading' => 'h2' ) );
			endwhile;
			?>
		</div>
		<?php lyk7_pagination(); ?>
	<?php else : ?>
		<?php lyk7_empty( 'Δεν υπάρχουν ανακοινώσεις σε αυτή την κατηγορία.' ); ?>
	<?php endif; ?>
</div>
<?php
get_footer();
