#!/usr/bin/env python
"""
Find whole sentences matching a regex in Project Gutenberg plain text files.
"""
from __future__ import print_function, unicode_literals
import re
import os
import sys
import glob
import codecs
import pickle
import argparse
import textwrap
import nltk.data

try:
    import timing
except ImportError:
    pass

SENTENCES_CACHE = "sentences_cache.pkl"
TOKENIZER = None


def load_cache(filename):
    data = None
    if os.path.isfile(filename):
        print("Open cache...")
        with open(filename, 'rb') as fp:
            data = pickle.load(fp)
    return data


def save_cache(filename, data):
    with open(filename, 'wb') as fp:
        pickle.dump(data, fp, -1)


# cmd.exe cannot do Unicode so encode first
def print_it(text):
    print(text.encode('utf-8'))


# Add thousands commas
def commafy(value):
    return "{:,}".format(value)


def format(text, indent=0, width=70):
    return textwrap.fill(text, width=width, initial_indent=" "*indent,
                         subsequent_indent=" "*indent)


def find_sentences_in_text(filename):
    """Read text from file and return a list of sentences"""
    global TOKENIZER
    print("Open " + filename + "...")
    try:
        with codecs.open(filename, encoding='cp1252') as fp:
            text = fp.read()

        print("Tokenize...")
        if TOKENIZER is None:
            TOKENIZER = nltk.data.load('tokenizers/punkt/english.pickle')
        sentences = TOKENIZER.tokenize(text)
        print(commafy(len(sentences)), "sentences found")

        return sentences
    except UnicodeDecodeError:
        return []


def load_sentences_from_files(files, regex=None, flags=0):
    all_sentences = []

    for i, filename in enumerate(files):
        print(i+1, "/", len(files))
        sentences = find_sentences_in_text(filename)

        all_sentences.extend(sentences)

    print(commafy(len(all_sentences)), "total sentences found")
    return all_sentences


def find_matching_sentences(regex, sentences, flags=0):
    matching_sentences = []
    for sentence in sentences:
        # if re.search(r"\b" + re.escape(word) + r"\b", sentence, flags):
        if re.search(regex, sentence, flags):
            # print("-"*80)
            # print_it(sentence)
            matching_sentences.append(sentence)
    return matching_sentences


def output(sentences, filename):
    with open(filename, "w") as fp:
        for s in sentences:
            s = s.replace("\r\n", " ")
            # s = s.replace(args.word, "**" + args.word + "**")  TODO
            out = format(s) + "\n\n"
            out = out.encode("utf-8")
            print(out)
            fp.write(out)
            # print("-"*80)


def insert_thing_into_filename(thing, filename):
    """Insert thing before the filename's extension"""
    root, ext = os.path.splitext(filename)
    filename = root + thing + ext
    return filename


def correct_those(sentences):
    for i, sentence in enumerate(sentences):
        if sentence.startswith('"') and not sentence.endswith('"'):
            sentences[i] = sentence + '"'
        elif sentence.startswith("'") and not sentence.endswith("'"):
            sentences[i] = sentence + "'"

        if not sentence.startswith('"') and sentence.endswith('"'):
            sentences[i] = '"' + sentence
        elif not sentence.startswith("'") and sentence.endswith("'"):
            sentences[i] = "'" + sentence
    return sentences


def gutengrep(regex, inspec, outfile, ignore_case,
              sort, cache, correct):

    if not inspec and not cache:
        sys.exit("Error: inspec and/or cache arguments needed")

    if inspec:
        files = glob.glob(inspec)
        if not files:
            sys.exit("No input files found matching " + inspec)

    if ignore_case:
        flags = re.IGNORECASE
    else:
        flags = 0

    sentences = None
    # Open
    if cache:
        sentences = load_cache(SENTENCES_CACHE)

    if not sentences:
        sentences = load_sentences_from_files(files)
        if cache:
            save_cache(SENTENCES_CACHE, sentences)

    print(commafy(len(sentences)), "sentences found")

    # Filter
    sentences = find_matching_sentences(regex, sentences, flags)

    if args.correct:
        sentences = correct_those(sentences)

    output(sentences, outfile)

    if sort:
        sentences.sort(key=len)
        print("*"*80)
        outfile = insert_thing_into_filename("-sort", outfile)
        output(sentences, outfile)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Find whole sentences matching a regex in "
                    "Project Gutenberg plain text files.",
                    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('regex', nargs=1,
                        help='Input regular expression e.g. "\\bword\\b"')
    parser.add_argument('inspec', nargs='?',
                        help="Input file spec")
    parser.add_argument('-o', '--outfile', default='output.log',
                        help="Output filename")
    parser.add_argument('-i', '--ignore-case', action='store_true',
                        help="Ignore case distinctions")
    parser.add_argument('-s', '--sort', action='store_true',
                        help="Also sort sentences by length and save in "
                             "file named like output-sort.log")
    # parser.add_argument('-b', '--bold', action='store_true',
    #                     help="Embolden found text TODO")
    parser.add_argument('--cache', action='store_true',
                        help="Load cache. If no cache, save one. Warning: "
                             "the cache is saved based on the initial "
                             "inspec. Subsequent uses are based on this "
                             "initial cache, effectively ignoring inspec. ")
    parser.add_argument('--correct', action='store_true',
                        help="Make little corrections to sentences, "
                             "like balancing quotes")
    args = parser.parse_args()

    gutengrep(args.regex[0], args.inspec, args.outfile, args.ignore_case,
              args.sort, args.cache, args.correct)

# End of file