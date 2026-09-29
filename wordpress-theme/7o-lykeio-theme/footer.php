<?php
/**
 * Site footer.
 *
 * @package lyk7
 */

$lyk7_phones = lyk7_phones();
$lyk7_email  = lyk7_opt( 'email' );
?>
</main>

<footer class="site-footer">
	<div class="wrap">

		<div class="footer-grid">

			<div class="footer-col footer-col--identity">
				<p class="footer-name"><?php bloginfo( 'name' ); ?></p>

				<address class="footer-address">
					<p>
						<?php lyk7_icon( 'pin', 17 ); ?>
						<span><?php echo esc_html( lyk7_opt( 'address' ) ); ?></span>
					</p>

					<?php foreach ( $lyk7_phones as $lyk7_row ) : ?>
						<p>
							<?php lyk7_icon( 'phone', 17 ); ?>
							<span>
								<span class="footer-address__label"><?php echo esc_html( $lyk7_row[0] ); ?>:</span>
								<?php
								$lyk7_links = array();
								foreach ( $lyk7_row[1] as $lyk7_num ) {
									$lyk7_links[] = '<a href="' . esc_attr( lyk7_tel( $lyk7_num ) ) . '">' . esc_html( $lyk7_num ) . '</a>';
								}
								echo implode( ' · ', $lyk7_links ); // phpcs:ignore WordPress.Security.EscapeOutput
								?>
							</span>
						</p>
					<?php endforeach; ?>

					<?php if ( $lyk7_email ) : ?>
						<p>
							<?php lyk7_icon( 'mail', 17 ); ?>
							<span><a href="mailto:<?php echo esc_attr( antispambot( $lyk7_email ) ); ?>"><?php echo esc_html( antispambot( $lyk7_email ) ); ?></a></span>
						</p>
					<?php endif; ?>
				</address>

				<?php if ( lyk7_opt( 'summer_note' ) ) : ?>
					<p class="footer-summer"><?php echo esc_html( lyk7_opt( 'summer_note' ) ); ?></p>
				<?php endif; ?>
			</div>

			<nav class="footer-col" aria-label="Γρήγοροι σύνδεσμοι">
				<h2 class="footer-heading">Γρήγοροι σύνδεσμοι</h2>
				<?php lyk7_nav( 'footer-quick', 'footer-menu' ); ?>
			</nav>

			<nav class="footer-col" aria-label="Χρήσιμοι σύνδεσμοι">
				<h2 class="footer-heading">Χρήσιμοι σύνδεσμοι</h2>
				<?php lyk7_nav( 'footer-external', 'footer-menu' ); ?>
			</nav>

			<div class="footer-col footer-col--hours">
				<h2 class="footer-heading">Ωράριο</h2>
				<ul class="footer-hours">
					<?php foreach ( lyk7_timetable() as $lyk7_row ) : ?>
						<li>
							<span><?php echo esc_html( $lyk7_row[0] ); ?></span>
							<span class="footer-hours__time"><?php echo esc_html( $lyk7_row[1] . '–' . $lyk7_row[2] ); ?></span>
						</li>
					<?php endforeach; ?>
				</ul>
			</div>

		</div>

		<div class="footer-bottom">
			<p class="footer-copy">© <?php echo esc_html( wp_date( 'Y' ) ); ?> <?php bloginfo( 'name' ); ?></p>

			<nav aria-label="Θεσμικές πληροφορίες">
				<?php lyk7_nav( 'legal', 'footer-legal' ); ?>
			</nav>

			<a class="footer-top" href="#top">
				Επιστροφή στην κορυφή
				<?php lyk7_icon( 'arrow', 15, 'is-up' ); ?>
			</a>
		</div>

	</div>
</footer>

<?php wp_footer(); ?>
</body>
</html>
