#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from analyser import analyser


def main():
    try:
        resultats = analyser()
        print("Analyse terminée")
        print(resultats)
    except Exception as e:
        print("Erreur :", e)


if __name__ == "__main__":
    main()