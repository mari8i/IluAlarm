import time
import settings

if settings.ON_rapRASPBERRY:
   import RPi.GPIO as GPIO

class RGBDisplay(object):

    def __init__(self, cs, rst, a0, clk, si):
        self.cs = cs
        self.rst = rst
        self.a0 = a0
        self.clk = clk
        self.si = si

        self.io_init()
        self.lcd_init()
        
        if not settings.ON_RASPBERRY:
           self.display = [[" "] * 16 for x in xrange(8)]
           
        return

    def io_init(self):
        if settings.ON_RASPBERRY:
            GPIO.setup(self.cs, GPIO.OUT)
            GPIO.setup(self.rst, GPIO.OUT)
            GPIO.setup(self.a0, GPIO.OUT)
            GPIO.setup(self.clk, GPIO.OUT)
            GPIO.setup(self.si, GPIO.OUT)
        else:
            print "[DISPLAY] IO Init"

        return

    def lcd_init(self):
        if settings.ON_RASPBERRY:
            GPIO.output(self.cs, True)
            GPIO.output(self.rst, False)
            GPIO.output(self.rst, True)
            self.lcd_tranfer_data(0xe2,0) # DEf: 0xe2
            self.lcd_tranfer_data(0xa3,0) # Def: 0xa3
            self.lcd_tranfer_data(0xa0,0) # 0xa0 -> normal, 0xa1 -> reversed
            self.lcd_tranfer_data(0xc8,0)
            self.lcd_tranfer_data(0xa4,0)
            self.lcd_tranfer_data(0xa7,0) # 0xa7 -> black text white bg, 0xa6 -> white text black bg
            self.lcd_tranfer_data(0x2f,0)
            self.lcd_tranfer_data(0x40,0)
            self.lcd_tranfer_data(0x22,0)
            self.lcd_tranfer_data(0x81,0)
            self.lcd_tranfer_data(0x28,0)
            self.lcd_tranfer_data(0xaf,0)

            # Set contrast (To max!)
            val = 100
            self.lcd_tranfer_data(0x81, 0)
            self.lcd_tranfer_data(0 | (val & 0x3f), 0)
            
            self.lcd_clear()
        else:
            print "[DISPLAY] LCD Init"
        return

    def print_screen(self):
        print "-" * 18
        for l in self.display:
            print "|" + "".join(l) + "|"
            pass
        print "-" * 18
        return

    def lcd_font_string(self, xPos, yPos, string, font):
       stringLen = len(string)       
       offset = 0
       
       for i in range(0, stringLen):
          char = ord(string[i]) - 32
          height = font['height']
          width = font['chars'][char][0]
          
          self.lcd_font(xPos + offset, yPos, char, font)

          offset += width + 1  # char width +  spacing between letters..

       if offset > 0:
          offset -= 1
          
       return offset

    def get_font_width(self, string, font):
       stringLen = len(string)       
       offset = 0
       
       for i in range(0, stringLen):
          char = ord(string[i]) - 32
          width = font['chars'][char][0]
          offset += width + 1  # char width +  spacing between letters..

       if offset > 0:
          offset -= 1
          
       return offset
       
    def lcd_font(self, xPos, yPos, char, font):
       yPos = (yPos + 4) % 8  # Workaround..
       
       height = font['height']
       width = font['chars'][char][0]
       bitmap = font['chars'][char][1:]

       # This should always be an integer..
       pages = len(bitmap) / width

       for y in xrange(pages):
          self.lcd_set_page((yPos + y) % 8, xPos)
          for i in range(width):
             self.lcd_tranfer_data(bitmap[(i * pages) + y], 1)
       return

    def lcd_area_clear(self, xPos, yPos, pages, width):
        yPos = (yPos + 4) % 8  # Workaround..
       
        if settings.ON_RASPBERRY:
            GPIO.output(self.cs, False)
            for p in xrange(pages):
               self.lcd_set_page(yPos + p, xPos)
               for _ in xrange(width):
                  self.lcd_tranfer_data(0x00,1)
                  
            GPIO.output(self.cs, True)
        else:
            print "[DISPLAY] Clear"

    def lcd_clear(self):
        if settings.ON_RASPBERRY:
            GPIO.output(self.cs, False)
            for i in range(0, 8):
                self.lcd_set_page(i,0)
                for j in range(0, 129):
                   self.lcd_tranfer_data(0x00,1)
            GPIO.output(self.cs, True)
        else:
            print "[DISPLAY] Clear"

    def lcd_set_page(self, page, column):
        # la colonna viene data da 0 a 128!!!!!!!!!!!!
        lsb = column & 0x0f # 15
        msb = column & 0xf0 # 240 | 11110000
        msb = msb >> 4  # / 16
        msb = msb | 0x10   # this is 16 |  00010000
        page = page | 0xb0 # 176 | 10110000
        self.lcd_tranfer_data(page,0)
        self.lcd_tranfer_data(msb, 0)
        self.lcd_tranfer_data(lsb, 0)


    def lcd_tranfer_data(self, value, SI):
        GPIO.output(self.cs, False)
        GPIO.output(self.clk, True)
        if SI:
            GPIO.output(self.a0, True)
        else:
            GPIO.output(self.a0, False)
        self.lcd_byte(value)
        GPIO.output(self.cs, True)


    def lcd_byte(self, bits):
        tmp = bits;
        for i in range(0, 8):
            GPIO.output(self.clk, False)
            if(tmp & 0x80):
                GPIO.output(self.si, True)
            else:
                GPIO.output(self.si, False)
            tmp = (tmp<<1)
            GPIO.output(self.clk, True)

        return
