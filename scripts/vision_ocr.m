#import <AppKit/AppKit.h>
#import <Foundation/Foundation.h>
#import <Vision/Vision.h>

static void print_usage(void) {
    fprintf(stderr, "Usage: vision_ocr <image-path> [language ...]\n");
}

int main(int argc, const char *argv[]) {
    @autoreleasepool {
        if (argc < 2) {
            print_usage();
            return 2;
        }

        NSString *imagePath = [NSString stringWithUTF8String:argv[1]];
        NSImage *image = [[NSImage alloc] initWithContentsOfFile:imagePath];
        CGImageRef cgImage = [image CGImageForProposedRect:NULL context:nil hints:nil];
        if (image == nil || cgImage == nil) {
            fprintf(stderr, "Unable to read image.\n");
            return 3;
        }

        NSMutableArray<NSString *> *languages = [NSMutableArray array];
        for (int index = 2; index < argc; index++) {
            [languages addObject:[NSString stringWithUTF8String:argv[index]]];
        }
        if (languages.count == 0) {
            [languages addObjectsFromArray:@[@"ko-KR", @"en-US"]];
        }

        VNRecognizeTextRequest *request = [[VNRecognizeTextRequest alloc] init];
        request.recognitionLevel = VNRequestTextRecognitionLevelAccurate;
        request.usesLanguageCorrection = YES;
        request.recognitionLanguages = languages;

        VNImageRequestHandler *handler = [[VNImageRequestHandler alloc] initWithCGImage:cgImage options:@{}];
        NSError *error = nil;
        if (![handler performRequests:@[request] error:&error]) {
            fprintf(stderr, "Vision OCR failed: %s\n", error.localizedDescription.UTF8String);
            return 4;
        }

        NSArray<VNRecognizedTextObservation *> *observations =
            [request.results sortedArrayUsingComparator:^NSComparisonResult(
                VNRecognizedTextObservation *left,
                VNRecognizedTextObservation *right
            ) {
                CGFloat verticalDifference = fabs(CGRectGetMaxY(left.boundingBox) - CGRectGetMaxY(right.boundingBox));
                if (verticalDifference > 0.015) {
                    return CGRectGetMaxY(left.boundingBox) > CGRectGetMaxY(right.boundingBox)
                        ? NSOrderedAscending
                        : NSOrderedDescending;
                }
                return CGRectGetMinX(left.boundingBox) < CGRectGetMinX(right.boundingBox)
                    ? NSOrderedAscending
                    : NSOrderedDescending;
            }];

        for (VNRecognizedTextObservation *observation in observations) {
            VNRecognizedText *candidate = [[observation topCandidates:1] firstObject];
            if (candidate != nil) {
                printf("%s\n", candidate.string.UTF8String);
            }
        }
    }
    return 0;
}
