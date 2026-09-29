<?php
/**
 * Contact details + timetable (homepage and the Επικοινωνία page).
 *
 * @package lyk7
 */

$lyk7_email = lyk7_opt( 'email' );
?>
<section class="section section--contact" id="epikoinonia" aria-labelledby="contact-title">
	<div class="wrap contact">

		<div class="contact__details" data-reveal>
			<p class="eyebrow">Πού θα μας βρείτε</p>
			<h2 class="section__title" id="contact-title">Επικοινωνία</h2>

			<dl class="contact__list">
				<div class="contact__row">
					<dt><?php lyk7_icon( 'pin', 19 ); ?> Διεύθυνση</dt>
					<dd><?php echo esc_html( lyk7_opt( 'address' ) ); ?></dd>
				</div>

				<?php foreach ( lyk7_phones() as $lyk7_i => $lyk7_row ) : ?>
					<div class="contact__row">
						<dt><?php lyk7_icon( $lyk7_i ? 'users' : 'phone', 19 ); ?> <?php echo esc_html( $lyk7_row[0] ); ?></dt>
						<dd>
							<?php
							$lyk7_links = array();
							foreach ( $lyk7_row[1] as $lyk7_num ) {
								$lyk7_links[] = '<a href="' . esc_attr( lyk7_tel( $lyk7_num ) ) . '">' . esc_html( $lyk7_num ) . '</a>';
							}
							echo implode( ' · ', $lyk7_links ); // phpcs:ignore WordPress.Security.EscapeOutput
							?>
						</dd>
					</div>
				<?php endforeach; ?>

				<?php if ( $lyk7_email ) : ?>
					<div class="contact__row">
						<dt><?php lyk7_icon( 'mail', 19 ); ?> Ηλεκτρονικό ταχυδρομείο</dt>
						<dd><a href="mailto:<?php echo esc_attr( antispambot( $lyk7_email ) ); ?>"><?php echo esc_html( antispambot( $lyk7_email ) ); ?></a></dd>
					</div>
				<?php endif; ?>
			</dl>

			<?php if ( lyk7_opt( 'summer_note' ) ) : ?>
				<p class="contact__note"><?php lyk7_icon( 'clock', 17 ); ?> <span><?php echo esc_html( lyk7_opt( 'summer_note' ) ); ?></span></p>
			<?php endif; ?>

			<?php if ( lyk7_opt( 'map_url' ) ) : ?>
				<a class="btn btn--secondary" href="<?php echo esc_url( lyk7_opt( 'map_url' ) ); ?>" target="_blank" rel="noopener noreferrer">Άνοιγμα στον χάρτη <?php lyk7_icon( 'external', 15 ); ?></a>
			<?php endif; ?>
		</div>

		<div class="contact__schedule" data-reveal>
			<table class="timetable">
				<caption>Ωράριο διδακτικών ωρών</caption>
				<thead>
					<tr><th scope="col">Ώρα</th><th scope="col">Έναρξη</th><th scope="col">Λήξη</th></tr>
				</thead>
				<tbody>
					<?php foreach ( lyk7_timetable() as $lyk7_row ) : ?>
						<tr>
							<th scope="row" data-label="Ώρα"><?php echo esc_html( $lyk7_row[0] ); ?></th>
							<td data-label="Έναρξη"><?php echo esc_html( $lyk7_row[1] ); ?></td>
							<td data-label="Λήξη"><?php echo esc_html( $lyk7_row[2] ); ?></td>
						</tr>
					<?php endforeach; ?>
				</tbody>
			</table>
		</div>

	</div>
</section>
