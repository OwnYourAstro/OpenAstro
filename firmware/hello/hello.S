/* OpenAstro minimal M*CORE hello for the XTS 2500.
 * This is a RAM payload, not a flash image. It assumes the FlashZap RAM
 * downloader has placed it at 0x12000400; this payload is linked at 0x12040000.
 */
    .text
    .equ LCD_DATA, 0x13000000
    .equ LCD_CMD,  0x13000001
    .equ LCD_INIT_LEN, 20
    .equ TEXT_LEN, 54
    .globl _start
_start:
    /* Match the vendor RAM downloader's initial CPU state; EIM is left alone. */
    lrw     r2, 0xA0000140
    mtcr    r2, psr
    lrw     r2, 0x12000400
    mtcr    r2, vbr
    lrw     r1, 0x00105FFC
    mov     r0, r1

    /* EIM is already configured by the bootloader/dloader; do not touch it. */

    /* LCD command/data ports. 0x13000000 carries display data;
     * 0x13000001 carries controller commands. */
    lrw     r10, LCD_CMD
    lrw     r11, lcd_init
    movi    r12, LCD_INIT_LEN
1:
    ldb     r1, (r11, 0)
    stb     r1, (r10, 0)
    addi    r11, 1
    decne   r12
    bt      1b

    /* Page 0, column 0, then one text line. */
    lrw     r10, LCD_CMD
    lrw     r1, 0xB0
    stb     r1, (r10, 0)
    movi    r1, 0x10
    stb     r1, (r10, 0)
    movi    r1, 0x00
    stb     r1, (r10, 0)

    lrw     r10, LCD_DATA
    lrw     r11, text_font
    movi    r12, TEXT_LEN
2:
    ldb     r1, (r11, 0)
    stb     r1, (r10, 0)
    addi    r11, 1
    decne   r12
    bt      2b

    /* Keep the image alive; there is no RTOS here. */
3:
    br      3b

    .section .rodata
lcd_init:
    /* Full bootloader display descriptor prefix plus initialization. */
    .byte   0xFD
    .byte   0xB0
    .byte   0x81, 0xFF
    .byte   0xAB
    .byte   0xE2
    .byte   0xAE
    .byte   0xC8
    .byte   0xA6
    .byte   0xA1
    .byte   0xA0
    .byte   0xA2
    .byte   0xE4
    .byte   0xAF
    .byte   0xC0
    .byte   0x85
    .byte   0xD0
    .byte   0xD3
    .byte   0xA8
    .byte   0xA9


text_font:
    /* "OpenAstro" in a compact 5x7, least-significant bit at the top. */
    .byte   0x3E,0x41,0x41,0x41,0x3E,0x00  /* O */
    .byte   0x7F,0x09,0x09,0x09,0x06,0x00  /* p */
    .byte   0x3E,0x49,0x49,0x49,0x26,0x00  /* e */
    .byte   0x7F,0x01,0x01,0x01,0x7E,0x00  /* n */
    .byte   0x7E,0x11,0x11,0x11,0x7E,0x00  /* A */
    .byte   0x26,0x49,0x49,0x49,0x32,0x00  /* s */
    .byte   0x04,0x04,0x7F,0x04,0x04,0x00  /* t */
    .byte   0x7F,0x09,0x09,0x09,0x01,0x00  /* r */
    .byte   0x3E,0x41,0x41,0x41,0x3E,0x00  /* o */

    /* Place the data after code; the absolute ports are literals. */
    .literals
