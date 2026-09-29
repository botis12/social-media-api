<?php
/**
 * Page.
 *
 * @package lyk7
 */

get_header();
lyk7_breadcrumbs();

while ( have_posts() ) :
	the_post();
	?>
	<article class="single single--page">
		<header class="single__head">
			<div class="wrap wrap--text">
				<h1 class="single__title"><?php the_title(); ?></h1>
				<?php if ( has_excerpt() ) : ?>
					<p class="single__lede"><?php echo esc_html( get_the_excerpt() ); ?></p>
				<?php endif; ?>
			</div>
		</header>

		<?php if ( has_post_thumbnail() ) : ?>
			<figure class="single__hero wrap"><?php the_post_thumbnail( 'lyk7-wide' ); ?></figure>
		<?php endif; ?>

		<div class="wrap wrap--text">
			<div class="prose">
				<?php
				the_content();
				wp_link_pages();
				?>
			</div>

			<?php
			$lyk7_children = get_pages( array( 'child_of' => get_the_ID(), 'parent' => get_the_ID(), 'sort_column' => 'menu_order,post_title' ) );
			if ( $lyk7_children ) :
				?>
				<nav class="subpages" aria-label="Υποσελίδες">
					<h2 class="subpages__title">Σε αυτή την ενότητα</h2>
					<ul class="subpages__list">
						<?php foreach ( $lyk7_children as $lyk7_child ) : ?>
							<li><a href="<?php echo esc_url( get_permalink( $lyk7_child ) ); ?>"><span><?php echo esc_html( get_the_title( $lyk7_child ) ); ?></span> <?php lyk7_icon( 'arrow', 17 ); ?></a></li>
						<?php endforeach; ?>
					</ul>
				</nav>
			<?php endif; ?>

			<?php
			if ( comments_open() || get_comments_number() ) {
				comments_template();
			}
			?>
		</div>
	</article>

	<?php
	if ( 'epikoinonia' === get_post_field( 'post_name' ) ) {
		get_template_part( 'template-parts/contact' );
	}
endwhile;

get_footer();
