/* LAB ONLY. avmd-replay <file.wav> [streak] [detectors_n] [mode]
 * Prints the time (s) at which mod_avmd would fire avmd::beep, or "none".
 * The input is 8 kHz mono 16-bit (what avmd sees after the PCMU decode). */
#include <stdio.h>
#include <switch.h>
#include "avmd_buffer.h"
#include "avmd_sma_buf.h"
#include "avmd_fir.h"
#define AVMD_SAMPLES_PER_MS(r, m) ((r) / (1000/(m)))
#define AVMD_BEEP_TIME (2)
#define AVMD_SINE_TIME (1*0.125)
#define AVMD_SINE_LEN(r) AVMD_SAMPLES_PER_MS((r), AVMD_SINE_TIME)
#define AVMD_BEEP_LEN(r) AVMD_SAMPLES_PER_MS((r), AVMD_BEEP_TIME)
#define AVMD_P (5)
#define AVMD_FRAME_TIME (20)
#define AVMD_FRAME_LEN(r) AVMD_SAMPLES_PER_MS((r), AVMD_FRAME_TIME)
#define AVMD_TO_HZ(r, f) (((r) * (f)) / (2.0 * M_PI))
#define AVMD_MIN_AMP (17.0)
#define AVMD_MIN_FREQUENCY (440.0)
#define AVMD_MAX_FREQUENCY (2000.0)
#define AVMD_VARIANCE_RSD_THRESHOLD (0.000025)
#define AVMD_AMPLITUDE_RSD_THRESHOLD (0.0148)
#include "avmd_types.inc"
#include "avmd_desa2.inc"
#include "avmd_decide.inc"
#include "avmd_sample.inc"

int main(int argc, char **argv) {
	FILE *f = fopen(argv[1], "rb"); if (!f) { perror(argv[1]); return 2; }
	unsigned char hdr[44]; if (fread(hdr, 1, 44, f) != 44) return 2;
	avmd_session_t s; memset(&s, 0, sizeof s);
	/* PR1 avmd.conf.xml */
	s.settings.require_continuous_streak = 1; s.settings.sample_n_continuous_streak = argc > 2 ? atoi(argv[2]) : 3;
	s.settings.sample_n_to_skip = 0; s.settings.require_continuous_streak_amp = 1;
	s.settings.sample_n_continuous_streak_amp = argc > 2 ? atoi(argv[2]) : 3;
	s.settings.simplified_estimation = 1; s.settings.mode = argc > 4 ? atoi(argv[4]) : AVMD_DETECT_BOTH;
	s.settings.detectors_n = argc > 3 ? atoi(argv[3]) : 36; s.settings.detectors_lagged_n = 1;
	/* init_avmd_session_data(): sized for 48 kHz */
	s.rate = 48000;
	INIT_CIRC_BUFFER(&s.b, (size_t) AVMD_BEEP_LEN(s.rate), (size_t) AVMD_FRAME_LEN(s.rate), NULL);
	size_t buf_sz = AVMD_BEEP_LEN((uint32_t)s.rate) / (uint32_t) AVMD_SINE_LEN(s.rate);
	int nd = s.settings.detectors_n + s.settings.detectors_lagged_n;
	s.detectors = calloc(nd, sizeof(struct avmd_detector));
	size_t pos[64]; enum avmd_detection_mode res[64];
	uint8_t idx = 0, resolution = 0, offset;
	struct avmd_buffer *bb;
	#define INITBUF(b, r, o) do { bb = (b); INIT_SMA_BUFFER(&bb->sma_b, buf_sz, NULL); INIT_SMA_BUFFER(&bb->sqa_b, buf_sz, NULL); \
		INIT_SMA_BUFFER(&bb->sma_b_fir, buf_sz, NULL); INIT_SMA_BUFFER(&bb->sqa_b_fir, buf_sz, NULL); \
		INIT_SMA_BUFFER(&bb->sma_amp_b, buf_sz, NULL); INIT_SMA_BUFFER(&bb->sqa_amp_b, buf_sz, NULL); \
		bb->amplitude_max = 0.0; bb->samples_streak = 0; bb->samples_streak_amp = 0; bb->resolution = (r); bb->offset = (o); } while (0)
	while (idx < s.settings.detectors_n) { ++resolution; offset = 0;
		while (offset < resolution && idx < s.settings.detectors_n) { INITBUF(&s.detectors[idx].buffer, resolution, offset); s.detectors[idx].s = &s; s.detectors[idx].idx = idx; ++offset; ++idx; } }
	for (idx = 0; idx < s.settings.detectors_lagged_n; idx++) { struct avmd_detector *d = &s.detectors[s.settings.detectors_n + idx];
		INITBUF(&d->buffer, 1, 0); d->s = &s; d->idx = s.settings.detectors_n + idx; }
	/* avmd_launch_threads(): each detector thread takes pos = s->pos once, at launch */
	for (int i = 0; i < nd; i++) { struct avmd_detector *d = &s.detectors[i]; d->result = AVMD_DETECT_NONE;
		d->lagged = i >= s.settings.detectors_n; d->lag = d->lagged ? (i - s.settings.detectors_n + 1) : 0; pos[i] = s.pos; res[i] = AVMD_DETECT_NONE; }
	/* SWITCH_ABC_TYPE_INIT: the read codec's rate */
	s.rate = 8000;
	int16_t fr[160]; size_t frame_n = 0;
	while (fread(fr, 2, 160, f) == 160) {
		/* avmd_process() */
		INSERT_INT16_FRAME(&s.b, fr, 160);
		for (int i = 0; i < nd; i++) {
			struct avmd_detector *d = &s.detectors[i];
			if (d->result != AVMD_DETECT_NONE) continue;
			d->samples = (frame_n == 0 ? 160 - AVMD_P : 160);
			/* avmd_detector_func(), one pass */
			uint8_t r = d->buffer.resolution, o = d->buffer.offset; size_t samples = d->samples;
			if (d->lagged == 1) { if (d->lag > 0) { --d->lag; d->result = res[i]; continue; } pos[i] += AVMD_P; }
			for (size_t n = 1; n <= samples; n++) {
				if (((n + o) % r) == 0) { res[i] = avmd_process_sample(&s, &s.b, n, pos[i], d); if (res[i] != AVMD_DETECT_NONE) break; }
			}
			d->result = res[i];
		}
		for (int i = 0; i < nd; i++) if (s.detectors[i].result != AVMD_DETECT_NONE) {
			printf("%.3f %d %d\n", (frame_n + 1) * 0.02, s.detectors[i].result, i); return 0; }
		++frame_n;
		if (frame_n == 1) s.pos += 160 - AVMD_P; else s.pos += 160;
		s.pos &= s.b.mask;
	}
	printf("none\n"); return 0;
}
