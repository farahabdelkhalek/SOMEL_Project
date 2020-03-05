DEFINES+=PROJECT_CONF_H=\"project-conf.h\"
CONTIKI_PROJECT = range-test
CONTIKI_TARGET_SOURCEFILES += rgb-bl-lcd.c

ifdef WITH_LCD
CFLAGS += -DLCD_ENABLED=$(WITH_LCD)
endif

ifdef WITH_SUBGHZ
CFLAGS += -DRF_SUBGHZ=$(WITH_SUBGHZ)
endif

all: $(CONTIKI_PROJECT)

CONTIKI = ../../../..
CONTIKI_WITH_RIME = 1
include $(CONTIKI)/Makefile.include
