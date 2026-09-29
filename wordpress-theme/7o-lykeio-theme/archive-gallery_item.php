<?php
/**
 * Photo gallery.
 *
 * @package lyk7
 */

get_header();
lyk7_breadcrumbs();
lyk7_page_head( 'Συλλογή φωτογραφιών', 'Εικόνες', 'Στιγμιότυπα από τους χώρους, τις τοιχογραφίες και τη ζωή του σχολείου.' );
?>
<div class="wrap section">
	<?php if ( have_posts() ) : ?>
		<ul class="mosaic mosaic--full" data-gallery>
			<?php
			while ( have_posts() ) :
				the_post();
				get_template_part( 'template-parts/mosaic-item', null, array( 'caption' => true ) );
			endwhile;
			?>
		</ul>
		<?php lyk7_pagination(); ?>
	<?php else : ?>
		<?php lyk7_empty( 'Δεν υπάρχουν φωτογραφίες ακόμη.' ); ?>
	<?php endif; ?>
</div>
<?php
get_footer();
