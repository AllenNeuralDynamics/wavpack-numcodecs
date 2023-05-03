// Demo program for in-memory WavPack decoding.

#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>

#include "wavpack/wavpack.h"

// This is the context for reading a memory-based "file"

typedef struct {
    unsigned char ungetc_char, ungetc_flag;
    unsigned char *sptr, *dptr, *eptr;
    int64_t total_bytes_read;
} WavpackReaderContext;


static int32_t raw_read_bytes (void *id, void *data, int32_t bcount)
{
    WavpackReaderContext *rcxt = (WavpackReaderContext *) id;
    unsigned char *outptr = (unsigned char *) data;

    while (bcount) {
        if (rcxt->ungetc_flag) {
            *outptr++ = rcxt->ungetc_char;
            rcxt->ungetc_flag = 0;
            bcount--;
        }
        else {
            size_t bytes_to_copy = rcxt->eptr - rcxt->dptr;

            if (!bytes_to_copy)
                break;

            if (bytes_to_copy > bcount)
                bytes_to_copy = bcount;

            memcpy (outptr, rcxt->dptr, bytes_to_copy);
            rcxt->total_bytes_read += bytes_to_copy;
            rcxt->dptr += bytes_to_copy;
            outptr += bytes_to_copy;
            bcount -= bytes_to_copy;
        }
    }

    return (int32_t)(outptr - (unsigned char *) data);
}

static int32_t raw_write_bytes (void *id, void *data, int32_t bcount)
{
    return 0;
}

static int64_t raw_get_pos (void *id)
{
    WavpackReaderContext *rcxt = (WavpackReaderContext *) id;
    return rcxt->dptr - rcxt->sptr;
}

static int raw_set_pos_abs (void *id, int64_t pos)
{
    return 1;
}

static int raw_set_pos_rel (void *id, int64_t delta, int mode)
{
    return 1;
}

static int raw_push_back_byte (void *id, int c)
{
    WavpackReaderContext *rcxt = (WavpackReaderContext *) id;
    rcxt->ungetc_char = c;
    rcxt->ungetc_flag = 1;
    return c;
}

static int64_t raw_get_length (void *id)
{
    WavpackReaderContext *rcxt = (WavpackReaderContext *) id;
    return rcxt->eptr - rcxt->sptr;
}

static int raw_can_seek (void *id)
{
    return 0;
}

static int raw_close_stream (void *id)
{
    return 0;
}

static WavpackStreamReader64 raw_reader = {
    raw_read_bytes, raw_write_bytes, raw_get_pos, raw_set_pos_abs, raw_set_pos_rel,
    raw_push_back_byte, raw_get_length, raw_can_seek, NULL, raw_close_stream
};

// This is the single function for completely decoding a WavPack file from memory to memory. This version is
// for 16-bit audio in any number of channels, and will error out if the source file is not 16-bit. The
// number of channels is written to the specified pointer, but it is assumed that the caller already knows
// this. The number of composite samples (i.e., frames) is returned.

#define BUFFER_SAMPLES 3750

size_t WavpackDecodeFile (void *source, size_t source_bytes, int *num_chans, int *bytes_per_sample,
                          void *destin_char, size_t destin_bytes, int num_threads)
{
    size_t total_samples = 0, max_samples;
    int32_t *temp_buffer = NULL;
    WavpackReaderContext raw_wv;
    WavpackContext *wpc;
    char error [80];
    int nch, bps;

    memset (&raw_wv, 0, sizeof (WavpackReaderContext));
    raw_wv.dptr = raw_wv.sptr = (unsigned char *) source;
    raw_wv.eptr = raw_wv.dptr + source_bytes;
    wpc = WavpackOpenFileInputEx64 (&raw_reader, &raw_wv, NULL, error, num_threads << OPEN_THREADS_SHFT, 0);

    if (!wpc) {
        fprintf (stderr, "error opening file: %s\n", error);
        return -1;
    }

    nch = WavpackGetNumChannels (wpc);
    bps = WavpackGetBytesPerSample (wpc);
    max_samples = WavpackGetNumSamples (wpc);

    int8_t *dest_int8 = destin_char;
    int16_t *dest_int16 = destin_char;
    int32_t *dest_int32 = destin_char;

    if (num_chans)
        *num_chans = nch;

    if (bytes_per_sample)
        *bytes_per_sample = bps;

    // fprintf (stderr, "WavPack decoding: bytes per sample %d - num chans %d - num samples %d\n", bps, nch, (int) max_samples);

    // if either the passed-in destination pointer or the byte count is zero, just
    // return the total number of samples available without decoding anything

    if (!destin_char || !destin_bytes) {
        WavpackCloseFile (wpc);
        return max_samples;
    }

    // if we're actually decoding, then we might have to terminate decoding early is there's not enough space

    max_samples = destin_bytes / bps / nch;

    if (bps != 4)
        temp_buffer = malloc (BUFFER_SAMPLES * nch * sizeof (int32_t));

    while (1) {
        int samples_to_decode = total_samples + BUFFER_SAMPLES > max_samples ?
            max_samples - total_samples :
            BUFFER_SAMPLES;
        int samples_decoded = WavpackUnpackSamples (wpc, temp_buffer ? temp_buffer : dest_int32, samples_to_decode);
        int samples_to_copy = samples_decoded * nch;

        if (!samples_decoded)
            break;

        if ((bps == 1) || (bps == 2)) 
        {
            int32_t *sptr = temp_buffer;

            switch (bps) {
                case 1:
                    while (samples_to_copy--)
                        *dest_int8++ = *sptr++;

                    break;

                case 2:
                    while (samples_to_copy--)
                        *dest_int16++ = *sptr++;

                    break;
            }
        }
        else
            dest_int32 += samples_to_copy;

        if ((total_samples += samples_decoded) == max_samples)
            break;
    }

    free (temp_buffer);
    WavpackCloseFile (wpc);
    return total_samples;
}
